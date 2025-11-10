document.addEventListener('DOMContentLoaded', function() {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    const previewSection = document.getElementById('previewSection');
    const previewImage = document.getElementById('previewImage');
    const removeBtn = document.getElementById('removeBtn');
    const analyzeBtn = document.getElementById('analyzeBtn');
    const loadingSection = document.getElementById('loadingSection');
    const resultsSection = document.getElementById('resultsSection');
    const feedbackContent = document.getElementById('feedbackContent');
    const newAnalysisBtn = document.getElementById('newAnalysisBtn');
    const errorSection = document.getElementById('errorSection');
    const errorMessage = document.getElementById('errorMessage');
    const tryAgainBtn = document.getElementById('tryAgainBtn');
    const create3dBtn = document.getElementById('create3dBtn');
    const result3dPreview = document.getElementById('result3dPreview');
    const result3dImage = document.getElementById('result3dImage');
    const download3dBtn = document.getElementById('download3dBtn');

    let selectedFile = null;
    let imagePreviewUrl = null;
    let tempFilename = null;
    let current3dImageUrl = null;

    // Click to upload
    uploadArea.addEventListener('click', () => {
        fileInput.click();
    });

    // File input change
    fileInput.addEventListener('change', (e) => {
        handleFile(e.target.files[0]);
    });

    // Drag and drop
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });

    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        const file = e.dataTransfer.files[0];
        if (file) {
            handleFile(file);
        }
    });

    function handleFile(file) {
        if (!file) return;

        // Validate file type
        const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/bmp', 'image/webp'];
        if (!validTypes.includes(file.type)) {
            showError('Invalid file type. Please upload an image file (JPG, PNG, GIF, BMP, or WebP).');
            return;
        }

        // Validate file size (16MB)
        if (file.size > 16 * 1024 * 1024) {
            showError('File size exceeds 16MB limit. Please upload a smaller image.');
            return;
        }

        selectedFile = file;
        const reader = new FileReader();
        
        reader.onload = (e) => {
            previewImage.src = e.target.result;
            imagePreviewUrl = e.target.result; // Store the preview URL for results display
            uploadArea.style.display = 'none';
            previewSection.style.display = 'block';
            hideError();
            hideResults();
        };

        reader.onerror = () => {
            showError('Failed to read the image file. Please try again.');
        };

        reader.readAsDataURL(file);
    }

    // Remove preview
    removeBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        resetUpload();
    });

    // Analyze button
    analyzeBtn.addEventListener('click', async () => {
        if (!selectedFile) return;

        // Show loading, hide other sections
        previewSection.style.display = 'none';
        loadingSection.style.display = 'block';
        hideError();
        hideResults();

        const formData = new FormData();
        formData.append('file', selectedFile);

        try {
            const response = await fetch('/analyze', {
                method: 'POST',
                body: formData
            });

            // Check if response is JSON
            let data;
            try {
                data = await response.json();
            } catch (e) {
                throw new Error('Invalid response from server. Please try again.');
            }

            if (!response.ok) {
                throw new Error(data.error || `Server error: ${response.status}`);
            }

            // Validate response structure
            if (!data.success || !data.feedback) {
                throw new Error('Invalid response format from server.');
            }

            // Store temp filename for 3D generation
            tempFilename = data.temp_filename;
            
            // Update image preview URL if provided
            if (data.image_data) {
                imagePreviewUrl = `data:image/png;base64,${data.image_data}`;
            }

            // Display results
            displayResults(data.feedback);
        } catch (error) {
            // Handle network errors
            if (error.name === 'TypeError' && error.message.includes('fetch')) {
                showError('Network error. Please check your connection and try again.');
            } else {
                showError(error.message || 'An error occurred while analyzing the floor plan. Please try again.');
            }
        } finally {
            loadingSection.style.display = 'none';
        }
    });

    function displayResults(feedback) {
        // Reset 3D view
        result3dPreview.style.display = 'none';
        create3dBtn.style.display = 'block';
        create3dBtn.disabled = false;
        create3dBtn.textContent = 'Create 3D View';
        
        // Format the feedback text with proper bullet points
        let formattedFeedback = feedback;
        
        // Split by lines to process properly
        let lines = formattedFeedback.split('\n');
        let formattedLines = [];
        let inList = false;
        let currentList = [];
        
        lines.forEach((line, index) => {
            line = line.trim();
            if (!line) {
                // Empty line - close list if open
                if (inList && currentList.length > 0) {
                    formattedLines.push('<ul>' + currentList.join('') + '</ul>');
                    currentList = [];
                    inList = false;
                }
                return;
            }
            
            // Check for section headers (lines with ** or lines ending with :)
            if (line.match(/^\*\*.*\*\*$/) || (line.match(/^[A-Z][^:]*:$/) && !line.match(/^[-••\d]/))) {
                // Close any open list
                if (inList && currentList.length > 0) {
                    formattedLines.push('<ul>' + currentList.join('') + '</ul>');
                    currentList = [];
                    inList = false;
                }
                // Convert markdown headers
                line = line.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
                // Convert to h3 if it looks like a header
                if (line.endsWith(':') && !line.match(/^[-••\d]/)) {
                    line = line.replace(/:$/, '');
                    formattedLines.push(`<h3>${line}</h3>`);
                } else {
                    formattedLines.push(`<h3>${line}</h3>`);
                }
            }
            // Check for bullet points (starting with -, •, or numbers)
            else if (line.match(/^[-••]\s+/) || line.match(/^\d+\.\s+/)) {
                inList = true;
                // Remove bullet marker and add as list item
                let listItem = line.replace(/^[-••]\s+/, '').replace(/^\d+\.\s+/, '');
                // Convert any markdown bold
                listItem = listItem.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
                currentList.push(`<li>${listItem}</li>`);
            }
            // Regular text line
            else {
                // Close list if open
                if (inList && currentList.length > 0) {
                    formattedLines.push('<ul>' + currentList.join('') + '</ul>');
                    currentList = [];
                    inList = false;
                }
                // Convert markdown bold
                line = line.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
                formattedLines.push(`<p>${line}</p>`);
            }
        });
        
        // Close any remaining list
        if (inList && currentList.length > 0) {
            formattedLines.push('<ul>' + currentList.join('') + '</ul>');
        }
        
        formattedFeedback = formattedLines.join('');
        
        // Display the image preview if available
        const resultImagePreview = document.getElementById('resultImagePreview');
        if (imagePreviewUrl) {
            resultImagePreview.innerHTML = `<img src="${imagePreviewUrl}" alt="Floor plan preview" class="result-preview-image">`;
        } else {
            resultImagePreview.innerHTML = '';
        }
        
        feedbackContent.innerHTML = formattedFeedback;
        resultsSection.style.display = 'block';
    }

    function showError(message) {
        errorMessage.textContent = message;
        errorSection.style.display = 'block';
        loadingSection.style.display = 'none';
        hideResults();
    }

    function hideError() {
        errorSection.style.display = 'none';
    }

    function hideResults() {
        resultsSection.style.display = 'none';
    }

    function resetUpload() {
        selectedFile = null;
        imagePreviewUrl = null;
        tempFilename = null;
        current3dImageUrl = null;
        fileInput.value = '';
        previewImage.src = '';
        result3dPreview.style.display = 'none';
        uploadArea.style.display = 'block';
        previewSection.style.display = 'none';
        hideError();
        hideResults();
    }

    // Create 3D view button
    create3dBtn.addEventListener('click', async () => {
        if (!tempFilename) {
            showError('No floor plan available for 3D generation.');
            return;
        }

        // Show loading
        create3dBtn.disabled = true;
        create3dBtn.textContent = 'Generating 3D View...';
        loadingSection.style.display = 'block';

        try {
            const response = await fetch('/generate_3d', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ temp_filename: tempFilename })
            });

            let data;
            try {
                data = await response.json();
            } catch (e) {
                throw new Error('Invalid response from server.');
            }

            if (!response.ok) {
                throw new Error(data.error || `Server error: ${response.status}`);
            }

            if (!data.success || !data.image_data) {
                throw new Error('Invalid response format from server.');
            }

            // Display 3D image
            current3dImageUrl = `data:${data.mime_type || 'image/png'};base64,${data.image_data}`;
            result3dImage.src = current3dImageUrl;
            result3dPreview.style.display = 'block';
            
            // Hide the create button after successful generation
            create3dBtn.style.display = 'none';

        } catch (error) {
            showError(error.message || 'Failed to generate 3D view. Please try again.');
        } finally {
            loadingSection.style.display = 'none';
            create3dBtn.disabled = false;
            create3dBtn.textContent = 'Create 3D View';
        }
    });

    // Download 3D image button
    download3dBtn.addEventListener('click', () => {
        if (!current3dImageUrl) return;

        const link = document.createElement('a');
        link.href = current3dImageUrl;
        link.download = 'floor-plan-3d-view.png';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    });

    // New analysis button
    newAnalysisBtn.addEventListener('click', () => {
        resetUpload();
    });

    // Try again button
    tryAgainBtn.addEventListener('click', () => {
        hideError();
        if (selectedFile) {
            previewSection.style.display = 'block';
        } else {
            uploadArea.style.display = 'block';
        }
    });
});

