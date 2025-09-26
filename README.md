# JPEG AI Web Pipeline

JPEG AI Encoding and Decoding pipeline for Node.js with Python backend support for LPIPS quality assessment.

## Features

- PNG image normalization using Sharp
- JPEG-AI encoding/decoding via external binary (configurable path)
- LPIPS (Learned Perceptual Image Patch Similarity) quality assessment on GPU
- Automatic quality optimization to meet target LPIPS scores
- Multiple output formats: .jai, .preview.png, .jpegai.json

## Setup

### Node.js Dependencies

```bash
npm install
```

### Python Environment Setup

1. Create and activate a Python virtual environment:

```bash
cd py
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install Python dependencies with CUDA support:

```bash
pip install -r requirements.txt
```

### Environment Variables

Set the path to your JPEG-AI encoder/decoder:

```bash
export JPEGAI_RS="/path/to/jpegai-rs/target/release"
```

## Usage

### Command Line Interface

```bash
# Basic usage
npm run jpegai input.png

# Specify output prefix
npm run jpegai input.png output_prefix

# Custom target LPIPS score
npm run jpegai --target_lpips 0.05 input.png

# Full command options
node jpegai_pipeline.js --target_lpips 0.045 --input input.png --output output_prefix
```

### Options

- `--target_lpips <value>`: Target LPIPS score (default: 0.045)
- `--input <file>`: Input PNG file
- `--output <prefix>`: Output file prefix
- `--help`: Show help message

## Pipeline Process

1. **PNG Normalization**: Converts input PNG to normalized format using Sharp
2. **Quality Testing**: Tests JPEG-AI encoding with quality values q=28,32 and bpp=0.15
3. **LPIPS Calculation**: Computes perceptual similarity scores using GPU-accelerated LPIPS
4. **Optimization**: Selects the smallest file size meeting the target LPIPS threshold
5. **Output Generation**: Creates final .jai, .preview.png, and .jpegai.json files

## Output Files

- `<prefix>.jai`: JPEG-AI encoded file
- `<prefix>.preview.png`: Decoded preview image
- `<prefix>.jpegai.json`: Metadata including LPIPS scores, file sizes, and processing results

## Python Tools

### JPEG-AI Bridge

```bash
python py/jpegai_bridge.py encode input.png output.jai --quality 32 --bpp 0.15
python py/jpegai_bridge.py decode input.jai output.png
```

### LPIPS Score Calculator

```bash
python py/lpips_score.py reference.png distorted.png
python py/lpips_score.py --no-gpu reference.png distorted.png  # CPU mode
```

## Requirements

- Node.js 14+
- Python 3.8+
- CUDA-capable GPU (recommended for LPIPS calculation)
- JPEG-AI encoder/decoder binary (set via JPEGAI_RS environment variable)

## Development

The pipeline follows these conventions:
- Snake_case naming for files and variables
- Arrow functions in JavaScript
- Modular Python scripts with CLI interfaces
- Comprehensive error handling and logging

## License

MIT
