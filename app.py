import os
import base64
import io
import shutil
from flask import Flask, request, jsonify, render_template, send_file
from werkzeug.utils import secure_filename
import google.generativeai as genai
from PIL import Image
from config import (
    GEMINI_API_KEY, GEMINI_MODEL, GEMINI_IMAGE_MODEL, MAX_FILE_SIZE,
    ALLOWED_EXTENSIONS, UPLOAD_FOLDER, allowed_file
)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Configure Gemini API
genai.configure(api_key=GEMINI_API_KEY)

def analyze_floor_plan(image_path):
    """
    Analyze floor plan image using Gemini VLM API
    Returns formatted bullet-point feedback
    """
    model = genai.GenerativeModel(GEMINI_MODEL)
    
    # Read image file
    with open(image_path, 'rb') as image_file:
        image_data = image_file.read()
    
    # Craft concise prompt for floor plan analysis
    prompt = """Analyze this floor plan and provide CRISP, CONCISE bullet-point feedback. Keep each point to ONE line maximum. Be direct and actionable.

Focus on these three areas:

**Accessibility (ADA Compliance):**
- Door widths (min 32"), clearances, wheelchair routes, ramps, bathroom accessibility

**Space Efficiency:**
- Room proportions, wasted space, layout optimization, traffic flow, storage

**Best Practices:**
- Room flow, natural light, privacy, functionality

IMPORTANT:
- Maximum 3-5 bullet points per category
- Each bullet = ONE short sentence (10-15 words max)
- Skip obvious/good features - only mention issues or improvements
- Use format: "• Issue: brief solution"
- Be direct, no explanations or context"""

    try:
        # Load image using PIL
        img = Image.open(image_path)
        
        # Generate content with image
        response = model.generate_content([prompt, img])
        
        if not response or not response.text:
            raise Exception("Empty response from Gemini API")
        
        return response.text
    except Exception as e:
        error_msg = str(e)
        if "API key" in error_msg or "authentication" in error_msg.lower() or "401" in error_msg or "403" in error_msg:
            raise Exception(f"Gemini API authentication failed. Please check your API key. Error: {error_msg}")
        elif "quota" in error_msg.lower() or "rate limit" in error_msg.lower():
            raise Exception("Gemini API quota exceeded. Please try again later.")
        elif "safety" in error_msg.lower():
            raise Exception("Content was blocked by safety filters. Please try a different image.")
        else:
            raise Exception(f"Gemini API error: {error_msg}")

def generate_3d_view_from_plan(image_path):
    """
    Generate a 3D isometric architectural view from floor plan
    
    IMPORTANT: Google's Gemini models analyze images but don't generate new images.
    This function creates a visual transformation of the original image with:
    - Enhanced contrast and brightness
    - 3D shadow effects
    - Dark background
    - Border highlights to simulate depth
    
    For true AI image generation, you would need Google's Imagen API or similar services.
    """
    img = Image.open(image_path)
    
    # Create a prompt for generating 3D isometric view
    prompt = """create a 3d isometric model from this floor plan. 3d isometric model kept on a dark surface
     at a 30 degree angle with studio lighting. studio lighting and soft shadows"""
    
    try:
        # Try using the image generation model first (if it exists)
        model = None
        response = None
        
        try:
            model = genai.GenerativeModel(GEMINI_IMAGE_MODEL)
            response = model.generate_content([prompt, img])
        except Exception as model_error:
            # Log the actual error for debugging
            error_str = str(model_error)
            print(f"Error with image model '{GEMINI_IMAGE_MODEL}': {error_str}")
            
            # Check if it's a model not found error
            error_lower = error_str.lower()
            if any(term in error_lower for term in ["model", "not found", "does not exist", "invalid", "not available"]):
                print(f"Image model '{GEMINI_IMAGE_MODEL}' not available, using standard model '{GEMINI_MODEL}'")
                model = genai.GenerativeModel(GEMINI_MODEL)
                # Standard Gemini models don't generate images, so we'll use text analysis
                # and return an enhanced version of the original image
                response = model.generate_content([prompt, img])
            else:
                # Re-raise the error with full details
                raise Exception(f"Error accessing image generation model: {error_str}")
        
        # Check if response contains an image
        if hasattr(response, 'candidates') and response.candidates:
            for candidate in response.candidates:
                if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                    for part in candidate.content.parts:
                        if hasattr(part, 'inline_data') and part.inline_data:
                            # Extract image data
                            img_data = base64.b64decode(part.inline_data.data)
                            img_3d = Image.open(io.BytesIO(img_data))
                            
                            # Save to bytes
                            img_bytes = io.BytesIO()
                            img_3d.save(img_bytes, format='PNG')
                            img_bytes.seek(0)
                            
                            return img_bytes, 'image/png'
        
        # If no image in response, try using the model's image generation capability
        # Some models return images differently - check for image data in response
        if hasattr(response, 'parts'):
            for part in response.parts:
                if hasattr(part, 'inline_data') and part.inline_data:
                    img_data = base64.b64decode(part.inline_data.data)
                    img_3d = Image.open(io.BytesIO(img_data))
                    img_bytes = io.BytesIO()
                    img_3d.save(img_bytes, format='PNG')
                    img_bytes.seek(0)
                    return img_bytes, 'image/png'
        
        # Fallback: Create enhanced visualization from original with 3D effects
        # Since Gemini doesn't generate images, we'll create a visual transformation
        print("No image generated by API, creating 3D transformation of original")
        
        # Convert to RGB if needed
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Create a 3D-like transformation
        from PIL import ImageEnhance, ImageFilter, ImageOps, ImageDraw
        import numpy as np
        
        width, height = img.size
        
        # Create enhanced version with better contrast and brightness
        img_3d = img.copy()
        
        # Enhance contrast and brightness for better 3D effect
        enhancer = ImageEnhance.Contrast(img_3d)
        img_3d = enhancer.enhance(1.3)
        
        enhancer = ImageEnhance.Brightness(img_3d)
        img_3d = enhancer.enhance(1.1)
        
        # Add sharpness
        enhancer = ImageEnhance.Sharpness(img_3d)
        img_3d = enhancer.enhance(1.2)
        
        # Create a shadow effect
        shadow = img_3d.copy()
        shadow = ImageOps.colorize(ImageOps.grayscale(shadow), black="#404040", white="#808080")
        
        # Create a new image with padding for shadow and dark background
        padding = 30
        new_width = width + padding * 2
        new_height = height + padding * 2
        result = Image.new('RGB', (new_width, new_height), color='#1a1a1a')  # Dark background
        
        # Paste shadow slightly offset to simulate depth
        shadow_offset = 8
        result.paste(shadow, (padding + shadow_offset, padding + shadow_offset))
        
        # Paste the main enhanced image
        result.paste(img_3d, (padding, padding))
        
        # Add a 3D border effect
        draw = ImageDraw.Draw(result)
        
        # Draw multiple borders for depth effect
        for i in range(3):
            border_color = f"#{hex(100 + i * 30)[2:]:0>2}" * 3  # Gradient border
            draw.rectangle([
                padding - i - 1, 
                padding - i - 1, 
                padding + width + i, 
                padding + height + i
            ], outline=border_color, width=1)
        
        # Add corner highlights for 3D effect
        highlight_color = "#ffffff"
        draw.line([padding, padding, padding + 20, padding], fill=highlight_color, width=2)
        draw.line([padding, padding, padding, padding + 20], fill=highlight_color, width=2)
        
        # Save to bytes
        img_bytes = io.BytesIO()
        result.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        return img_bytes, 'image/png'
        
    except Exception as e:
        error_msg = str(e)
        error_lower = error_msg.lower()
        
        # Check for model not found errors first
        if "model" in error_lower and ("not found" in error_lower or "does not exist" in error_lower or "invalid" in error_lower):
            # Try falling back to the standard vision model
            try:
                print(f"Image model not available, trying fallback to {GEMINI_MODEL}")
                fallback_model = genai.GenerativeModel(GEMINI_MODEL)
                response = fallback_model.generate_content([prompt, img])
                # Since standard Gemini models don't generate images, return enhanced original
                img_3d = img.copy()
                if img_3d.mode != 'RGB':
                    img_3d = img_3d.convert('RGB')
                img_bytes = io.BytesIO()
                img_3d.save(img_bytes, format='PNG')
                img_bytes.seek(0)
                return img_bytes, 'image/png'
            except Exception as fallback_error:
                raise Exception(f"Image generation model unavailable. Error: {error_msg}. Fallback also failed: {str(fallback_error)}")
        elif "API key" in error_msg or "authentication" in error_lower or "401" in error_msg or "403" in error_msg:
            raise Exception(f"Gemini API authentication failed: {error_msg}")
        elif "quota" in error_lower or "rate limit" in error_lower or "429" in error_msg:
            # Show the actual error message for quota issues with more context
            raise Exception(f"Gemini API quota/rate limit error. Full error: {error_msg}. This might also indicate the model '{GEMINI_IMAGE_MODEL}' is not available. Please check your API key permissions and available models.")
        else:
            # Show the full error message for debugging
            raise Exception(f"3D generation error: {error_msg}. Model attempted: {GEMINI_IMAGE_MODEL}")

@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')

@app.errorhandler(413)
def request_entity_too_large(error):
    """Handle file size limit exceeded"""
    return jsonify({'error': 'File size exceeds the 16MB limit'}), 413

@app.route('/analyze', methods=['POST'])
def analyze():
    """Handle image upload and analysis"""
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        # Check if file is selected
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Validate file type
        if not allowed_file(file.filename):
            return jsonify({
                'error': f'Invalid file type. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}'
            }), 400
        
        # Check file size before saving
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)  # Reset file pointer
        
        if file_size > MAX_FILE_SIZE:
            return jsonify({
                'error': f'File size ({file_size / (1024*1024):.2f}MB) exceeds the 16MB limit'
            }), 400
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        try:
            file.save(filepath)
            
            # Verify file was saved and is readable
            if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
                raise Exception('Failed to save file or file is empty')
            
            # Analyze the floor plan
            feedback = analyze_floor_plan(filepath)
            
            # Read image as base64 for frontend use
            with open(filepath, 'rb') as img_file:
                img_base64 = base64.b64encode(img_file.read()).decode('utf-8')
            
            # Store filepath temporarily (will be cleaned up after 3D generation or timeout)
            # For now, keep the file for 3D generation
            temp_filename = f"temp_{filename}"
            temp_filepath = os.path.join(app.config['UPLOAD_FOLDER'], temp_filename)
            shutil.copy2(filepath, temp_filepath)
            
            return jsonify({
                'success': True,
                'feedback': feedback,
                'image_data': img_base64,
                'temp_filename': temp_filename
            })
        except Exception as e:
            # Clean up file on error
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                except:
                    pass
            return jsonify({'error': str(e)}), 500
            
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/generate_3d', methods=['POST'])
def generate_3d():
    """Generate 3D isometric view from floor plan"""
    try:
        data = request.get_json()
        temp_filename = data.get('temp_filename')
        
        if not temp_filename:
            return jsonify({'error': 'No image file provided'}), 400
        
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], temp_filename)
        
        if not os.path.exists(filepath):
            return jsonify({'error': 'Image file not found'}), 404
        
        try:
            # Generate 3D view
            img_bytes, mime_type = generate_3d_view_from_plan(filepath)
            
            # Convert to base64 for frontend
            img_base64 = base64.b64encode(img_bytes.read()).decode('utf-8')
            
            # Clean up temporary file
            if os.path.exists(filepath):
                os.remove(filepath)
            
            return jsonify({
                'success': True,
                'image_data': img_base64,
                'mime_type': mime_type
            })
        except Exception as e:
            # Clean up file on error
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                except:
                    pass
            return jsonify({'error': str(e)}), 500
            
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

