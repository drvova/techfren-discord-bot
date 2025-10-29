"""
Test image compression functionality
"""
import pytest
from PIL import Image
import io
from image_handler import compress_image

def create_test_image(width: int, height: int, mode: str = 'RGB', fmt: str = 'PNG') -> bytes:
    """Create a test image and return its bytes"""
    img = Image.new(mode, (width, height), color='red')
    output = io.BytesIO()
    img.save(output, format=fmt)
    return output.getvalue()

def test_compress_large_image():
    """Test compressing a large image"""
    # Create a 2048x2048 test image
    large_image = create_test_image(2048, 2048, fmt='JPEG')
    print(f"Original size: {len(large_image)} bytes")
    
    # Compress to 512x512
    compressed = compress_image(large_image, max_size=512, quality=85)
    print(f"Compressed size: {len(compressed)} bytes")
    
    # Verify compression worked
    assert len(compressed) < len(large_image), "Compressed image should be smaller"
    
    # Verify it's a valid image
    img = Image.open(io.BytesIO(compressed))
    assert img.format == 'JPEG', "Should be JPEG format"
    assert max(img.size) <= 512, "Should be resized to max 512px"
    print(f"✓ Compressed from {2048}x{2048} to {img.size[0]}x{img.size[1]}")

def test_compress_rgba_image():
    """Test compressing an RGBA image (converts to RGB)"""
    # Create RGBA test image
    rgba_image = create_test_image(1024, 1024, mode='RGBA')
    
    # Compress
    compressed = compress_image(rgba_image, max_size=512, quality=85)
    
    # Verify it's valid RGB JPEG
    img = Image.open(io.BytesIO(compressed))
    assert img.mode == 'RGB', "Should be converted to RGB"
    assert img.format == 'JPEG', "Should be JPEG format"
    print("✓ RGBA image converted to RGB")

def test_compress_small_image():
    """Test that small images aren't resized but still compressed"""
    # Create a 256x256 test image
    small_image = create_test_image(256, 256)
    original_size = len(small_image)
    
    # Compress (max_size=512, so shouldn't resize)
    compressed = compress_image(small_image, max_size=512, quality=85)
    
    # Should still compress (format conversion)
    assert len(compressed) < original_size, "Should still compress even if not resized"
    
    # Verify dimensions unchanged
    img = Image.open(io.BytesIO(compressed))
    assert img.size == (256, 256), "Small image dimensions should be preserved"
    print(f"✓ Small image not resized, but compressed from {original_size} to {len(compressed)} bytes")

def test_compression_ratio():
    """Test compression achieves good ratio"""
    # Create a large test image
    large_image = create_test_image(2048, 2048, fmt='JPEG')
    original_size = len(large_image)
    
    # Compress
    compressed = compress_image(large_image, max_size=512, quality=85)
    compressed_size = len(compressed)
    
    # Calculate ratio
    ratio = compressed_size / original_size * 100
    print(f"✓ Compression ratio: {ratio:.1f}%")
    
    # Should achieve at least 85% reduction for large images
    assert ratio < 15, f"Should compress to less than 15% of original (got {ratio:.1f}%)"

def test_different_quality_levels():
    """Test different quality levels"""
    test_image = create_test_image(1024, 1024)
    
    # Test different qualities
    quality_sizes = {}
    for quality in [50, 70, 85, 95]:
        compressed = compress_image(test_image, max_size=512, quality=quality)
        quality_sizes[quality] = len(compressed)
        print(f"Quality {quality}: {len(compressed)} bytes")
    
    # Lower quality should produce smaller files
    assert quality_sizes[50] < quality_sizes[95], "Lower quality should be smaller"
    print("✓ Quality levels work correctly")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
