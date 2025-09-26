#!/usr/bin/env python3
"""
LPIPS Score Calculator
Computes LPIPS (Learned Perceptual Image Patch Similarity) score between two images
Uses GPU acceleration when available
"""

import sys
import argparse
import torch
import lpips
from PIL import Image
import numpy as np
from pathlib import Path


class LPIPSCalculator:
    def __init__(self, use_gpu=True):
        """
        Initialize LPIPS calculator
        
        Args:
            use_gpu: Use GPU if available (default: True)
        """
        self.device = torch.device('cuda' if use_gpu and torch.cuda.is_available() else 'cpu')
        print(f"Using device: {self.device}", file=sys.stderr)
        
        # Initialize LPIPS model (using AlexNet backbone by default)
        self.lpips_model = lpips.LPIPS(net='alex').to(self.device)
        
        print("LPIPS model loaded successfully", file=sys.stderr)
    
    def load_and_preprocess_image(self, image_path):
        """
        Load and preprocess image for LPIPS calculation
        
        Args:
            image_path: Path to image file
            
        Returns:
            torch.Tensor: Preprocessed image tensor
        """
        # Load image
        image = Image.open(image_path)
        
        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Convert to numpy array and normalize to [0, 1]
        image_array = np.array(image).astype(np.float32) / 255.0
        
        # Convert to torch tensor and add batch dimension
        # Shape: (1, H, W, 3) -> (1, 3, H, W)
        image_tensor = torch.from_numpy(image_array).permute(2, 0, 1).unsqueeze(0)
        
        # Normalize to [-1, 1] range as expected by LPIPS
        image_tensor = image_tensor * 2.0 - 1.0
        
        return image_tensor.to(self.device)
    
    def calculate_lpips(self, image1_path, image2_path):
        """
        Calculate LPIPS score between two images
        
        Args:
            image1_path: Path to first image (reference)
            image2_path: Path to second image (distorted)
            
        Returns:
            float: LPIPS score (lower is better, 0 = identical)
        """
        # Load and preprocess images
        img1_tensor = self.load_and_preprocess_image(image1_path)
        img2_tensor = self.load_and_preprocess_image(image2_path)
        
        # Ensure images have the same size
        if img1_tensor.shape != img2_tensor.shape:
            raise ValueError(f"Images must have the same dimensions. "
                           f"Got {img1_tensor.shape} and {img2_tensor.shape}")
        
        # Calculate LPIPS score
        with torch.no_grad():
            lpips_score = self.lpips_model(img1_tensor, img2_tensor)
        
        return lpips_score.item()


def main():
    parser = argparse.ArgumentParser(description='Calculate LPIPS score between two images')
    parser.add_argument('image1', help='Path to reference image')
    parser.add_argument('image2', help='Path to distorted image')
    parser.add_argument('--no-gpu', action='store_true', help='Disable GPU usage')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    # Validate input files
    if not Path(args.image1).exists():
        print(f"Error: Reference image not found: {args.image1}", file=sys.stderr)
        sys.exit(1)
    
    if not Path(args.image2).exists():
        print(f"Error: Distorted image not found: {args.image2}", file=sys.stderr)
        sys.exit(1)
    
    try:
        # Initialize LPIPS calculator
        use_gpu = not args.no_gpu
        calculator = LPIPSCalculator(use_gpu=use_gpu)
        
        if args.verbose:
            print(f"Calculating LPIPS between:", file=sys.stderr)
            print(f"  Reference: {args.image1}", file=sys.stderr)
            print(f"  Distorted: {args.image2}", file=sys.stderr)
        
        # Calculate LPIPS score
        score = calculator.calculate_lpips(args.image1, args.image2)
        
        if args.verbose:
            print(f"LPIPS score: {score:.6f}", file=sys.stderr)
        
        # Output score to stdout (for parsing by other tools)
        print(f"{score:.6f}")
        
    except Exception as e:
        print(f"Error calculating LPIPS: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()