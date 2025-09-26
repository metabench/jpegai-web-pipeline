#!/usr/bin/env python3
"""
JPEG-AI Bridge
Provides encoding/decoding interface for JPEG-AI via external encoder/decoder
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path


def run_jpegai_command(command_args):
    """Run JPEG-AI command and return result"""
    try:
        result = subprocess.run(
            command_args,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"JPEG-AI command failed: {e.stderr}")


def encode_jpeg_ai(input_path, output_path, quality=32, bpp=0.15):
    """
    Encode PNG to JPEG-AI format
    
    Args:
        input_path: Path to input PNG file
        output_path: Path to output .jai file  
        quality: Quality parameter (default: 32)
        bpp: Bits per pixel parameter (default: 0.15)
    """
    jpegai_rs_path = os.environ.get('JPEGAI_RS')
    if not jpegai_rs_path:
        raise RuntimeError("JPEGAI_RS environment variable not set")
    
    encoder_path = Path(jpegai_rs_path) / "encode"
    if not encoder_path.exists():
        raise RuntimeError(f"JPEG-AI encoder not found at {encoder_path}")
    
    # Construct encoder command
    # Note: This is a placeholder - actual command structure depends on the JPEG-AI implementation
    command_args = [
        str(encoder_path),
        str(input_path),
        str(output_path),
        "--quality", str(quality),
        "--bpp", str(bpp)
    ]
    
    print(f"Encoding: {input_path} -> {output_path}")
    print(f"Quality: {quality}, BPP: {bpp}")
    
    return run_jpegai_command(command_args)


def decode_jpeg_ai(input_path, output_path):
    """
    Decode JPEG-AI to PNG format
    
    Args:
        input_path: Path to input .jai file
        output_path: Path to output PNG file
    """
    jpegai_rs_path = os.environ.get('JPEGAI_RS')
    if not jpegai_rs_path:
        raise RuntimeError("JPEGAI_RS environment variable not set")
    
    decoder_path = Path(jpegai_rs_path) / "decode"
    if not decoder_path.exists():
        raise RuntimeError(f"JPEG-AI decoder not found at {decoder_path}")
    
    # Construct decoder command
    command_args = [
        str(decoder_path),
        str(input_path),
        str(output_path)
    ]
    
    print(f"Decoding: {input_path} -> {output_path}")
    
    return run_jpegai_command(command_args)


def main():
    parser = argparse.ArgumentParser(description='JPEG-AI Bridge')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Encode command
    encode_parser = subparsers.add_parser('encode', help='Encode PNG to JPEG-AI')
    encode_parser.add_argument('input', help='Input PNG file')
    encode_parser.add_argument('output', help='Output .jai file')
    encode_parser.add_argument('--quality', type=int, default=32, help='Quality parameter (default: 32)')
    encode_parser.add_argument('--bpp', type=float, default=0.15, help='Bits per pixel (default: 0.15)')
    
    # Decode command
    decode_parser = subparsers.add_parser('decode', help='Decode JPEG-AI to PNG')
    decode_parser.add_argument('input', help='Input .jai file')
    decode_parser.add_argument('output', help='Output PNG file')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == 'encode':
            result = encode_jpeg_ai(args.input, args.output, args.quality, args.bpp)
            print(f"Encoding completed: {result}")
        elif args.command == 'decode':
            result = decode_jpeg_ai(args.input, args.output)
            print(f"Decoding completed: {result}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()