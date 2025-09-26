#!/usr/bin/env node

const fs = require('fs').promises;
const path = require('path');
const { spawn } = require('child_process');
const sharp = require('sharp');

// Default configuration
const DEFAULT_CONFIG = {
    target_lpips: 0.045,
    quality_rates: [28, 32],
    bpp_rate: 0.15,
    jpegai_rs_path: process.env.JPEGAI_RS
};

const parse_args = () => {
    const args = process.argv.slice(2);
    const config = { ...DEFAULT_CONFIG };
    
    for (let i = 0; i < args.length; i++) {
        switch (args[i]) {
            case '--target_lpips':
                config.target_lpips = parseFloat(args[++i]);
                break;
            case '--input':
                config.input = args[++i];
                break;
            case '--output':
                config.output = args[++i];
                break;
            case '--help':
                show_help();
                process.exit(0);
                break;
            default:
                if (!config.input) {
                    config.input = args[i];
                } else if (!config.output) {
                    config.output = args[i];
                }
        }
    }
    
    if (!config.input) {
        console.error('Error: Input file required');
        show_help();
        process.exit(1);
    }
    
    if (!config.output) {
        config.output = path.join(path.dirname(config.input), 
            path.basename(config.input, path.extname(config.input)));
    }
    
    if (!config.jpegai_rs_path) {
        console.error('Error: JPEGAI_RS environment variable not set');
        process.exit(1);
    }
    
    return config;
};

const show_help = () => {
    console.log(`
JPEG AI Web Pipeline

Usage: node jpegai_pipeline.js [options] <input.png> [output_prefix]

Options:
  --target_lpips <value>  Target LPIPS score (default: 0.045)
  --input <file>          Input PNG file
  --output <prefix>       Output file prefix
  --help                  Show this help

Environment Variables:
  JPEGAI_RS              Path to JPEG-AI encoder/decoder

Outputs:
  <prefix>.jai           JPEG-AI encoded file
  <prefix>.preview.png   Preview image
  <prefix>.jpegai.json   Metadata and results
`);
};

const normalize_png = async (input_path, output_path) => {
    try {
        await sharp(input_path)
            .png({ quality: 100, compressionLevel: 0 })
            .toFile(output_path);
        console.log(`Normalized PNG: ${output_path}`);
    } catch (error) {
        throw new Error(`PNG normalization failed: ${error.message}`);
    }
};

const run_python_script = (script_path, args) => {
    return new Promise((resolve, reject) => {
        const python_process = spawn('python', [script_path, ...args]);
        let stdout = '';
        let stderr = '';
        
        python_process.stdout.on('data', (data) => {
            stdout += data.toString();
        });
        
        python_process.stderr.on('data', (data) => {
            stderr += data.toString();
        });
        
        python_process.on('close', (code) => {
            if (code === 0) {
                resolve({ stdout: stdout.trim(), stderr: stderr.trim() });
            } else {
                reject(new Error(`Python script failed with code ${code}: ${stderr}`));
            }
        });
    });
};

const process_with_jpegai = async (normalized_path, jpegai_path, quality, bpp, output_prefix) => {
    const temp_jai = `${output_prefix}_temp_q${quality}.jai`;
    const temp_decoded = `${output_prefix}_temp_q${quality}_decoded.png`;
    
    try {
        // Encode with JPEG-AI
        const encode_result = await run_python_script('py/jpegai_bridge.py', [
            'encode', normalized_path, temp_jai, '--quality', quality.toString(), '--bpp', bpp.toString()
        ]);
        
        // Decode for comparison
        const decode_result = await run_python_script('py/jpegai_bridge.py', [
            'decode', temp_jai, temp_decoded
        ]);
        
        // Calculate LPIPS
        const lpips_result = await run_python_script('py/lpips_score.py', [
            normalized_path, temp_decoded
        ]);
        
        const lpips_score = parseFloat(lpips_result.stdout);
        const file_stats = await fs.stat(temp_jai);
        
        return {
            quality,
            bpp,
            lpips_score,
            file_size: file_stats.size,
            encoded_path: temp_jai,
            decoded_path: temp_decoded
        };
    } catch (error) {
        // Cleanup temp files on error
        try { await fs.unlink(temp_jai); } catch {}
        try { await fs.unlink(temp_decoded); } catch {}
        throw error;
    }
};

const find_best_quality = (results, target_lpips) => {
    // Filter results that meet the LPIPS target
    const valid_results = results.filter(r => r.lpips_score <= target_lpips);
    
    if (valid_results.length === 0) {
        console.warn(`Warning: No results met target LPIPS ${target_lpips}. Using best available.`);
        return results.reduce((best, current) => 
            current.lpips_score < best.lpips_score ? current : best
        );
    }
    
    // Among valid results, pick the smallest file size
    return valid_results.reduce((best, current) => 
        current.file_size < best.file_size ? current : best
    );
};

const cleanup_temp_files = async (results, best_result) => {
    for (const result of results) {
        if (result !== best_result) {
            try {
                await fs.unlink(result.encoded_path);
                await fs.unlink(result.decoded_path);
            } catch (error) {
                console.warn(`Warning: Could not cleanup temp file: ${error.message}`);
            }
        }
    }
};

const main = async () => {
    try {
        const config = parse_args();
        
        console.log('Starting JPEG AI Web Pipeline...');
        console.log(`Input: ${config.input}`);
        console.log(`Target LPIPS: ${config.target_lpips}`);
        
        // Step 1: Normalize PNG
        const normalized_path = `${config.output}_normalized.png`;
        await normalize_png(config.input, normalized_path);
        
        // Step 2: Process with different quality settings
        const results = [];
        for (const quality of config.quality_rates) {
            console.log(`Processing with quality ${quality}...`);
            try {
                const result = await process_with_jpegai(
                    normalized_path, config.jpegai_rs_path, quality, 
                    config.bpp_rate, config.output
                );
                results.push(result);
                console.log(`Quality ${quality}: LPIPS=${result.lpips_score.toFixed(4)}, Size=${result.file_size} bytes`);
            } catch (error) {
                console.error(`Failed to process quality ${quality}: ${error.message}`);
            }
        }
        
        if (results.length === 0) {
            throw new Error('No successful processing results');
        }
        
        // Step 3: Find best quality
        const best_result = find_best_quality(results, config.target_lpips);
        console.log(`Selected quality ${best_result.quality} (LPIPS: ${best_result.lpips_score.toFixed(4)})`);
        
        // Step 4: Generate final outputs
        const final_jai = `${config.output}.jai`;
        const final_preview = `${config.output}.preview.png`;
        const final_json = `${config.output}.jpegai.json`;
        
        await fs.rename(best_result.encoded_path, final_jai);
        await fs.rename(best_result.decoded_path, final_preview);
        
        // Create metadata JSON
        const metadata = {
            input_file: config.input,
            target_lpips: config.target_lpips,
            selected_quality: best_result.quality,
            selected_bpp: best_result.bpp,
            final_lpips: best_result.lpips_score,
            final_size: best_result.file_size,
            results: results,
            timestamp: new Date().toISOString()
        };
        
        await fs.writeFile(final_json, JSON.stringify(metadata, null, 2));
        
        // Step 5: Cleanup
        await cleanup_temp_files(results, best_result);
        await fs.unlink(normalized_path);
        
        console.log('\nPipeline completed successfully!');
        console.log(`Generated files:`);
        console.log(`  ${final_jai}`);
        console.log(`  ${final_preview}`);
        console.log(`  ${final_json}`);
        
    } catch (error) {
        console.error(`Pipeline failed: ${error.message}`);
        process.exit(1);
    }
};

if (require.main === module) {
    main();
}

module.exports = { 
    normalize_png, 
    process_with_jpegai, 
    find_best_quality, 
    DEFAULT_CONFIG 
};