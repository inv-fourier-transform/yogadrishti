import { useState, useRef, useEffect } from 'react';

export default function FileUpload({ onUpload, config }) {
  const [isDragging, setIsDragging] = useState(false);
  const [preview, setPreview] = useState(null);
  const [selectedFile, setSelectedFile] = useState(null);
  const fileInputRef = useRef(null);

  useEffect(() => {
    return () => {
      if (preview && preview.url) {
        URL.revokeObjectURL(preview.url);
      }
    };
  }, [preview]);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setIsDragging(true);
    } else if (e.type === "dragleave") {
      setIsDragging(false);
    }
  };

  const validateFile = (file) => {
    if (!file) return false;
    
    // Quick frontend validation matching backend settings
    const isVideo = file.type.startsWith('video/');
    const maxMb = isVideo ? (config?.max_video_size_mb || 100) : (config?.max_image_size_mb || 10);
    const maxSize = maxMb * 1024 * 1024;
    
    if (file.size > maxSize) {
      alert(`File is too large. Maximum size is ${maxMb}MB.`);
      return false;
    }
    
    return true;
  };

  const processFile = (file) => {
    if (!validateFile(file)) return;
    
    setSelectedFile(file);
    
    // Create preview
    const isVideo = file.type.startsWith('video/');
    const url = URL.createObjectURL(file);
    setPreview({ url, isVideo, name: file.name });
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      processFile(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      processFile(e.target.files[0]);
    }
  };

  const clearSelection = () => {
    setSelectedFile(null);
    setPreview(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const submitAnalysis = () => {
    if (selectedFile) onUpload(selectedFile);
  };

  if (preview) {
    return (
      <div className="file-preview-wrapper">
        <div className="preview-container">
          {preview.isVideo ? (
            <video src={preview.url} controls muted></video>
          ) : (
            <img src={preview.url} alt="Pose preview" />
          )}
          <div className="preview-overlay">
            <span className="file-name">{preview.name}</span>
            <button className="remove-btn" onClick={clearSelection}>✕ Remove</button>
          </div>
        </div>
        <div style={{marginTop: '20px', textAlign: 'center'}}>
          <button className="btn btn-primary btn-lg" onClick={submitAnalysis}>
            Analyze This Pose
          </button>
        </div>
      </div>
    );
  }

  return (
    <div 
      className={`upload-zone ${isDragging ? 'dragover' : ''}`}
      onDragEnter={handleDrag}
      onDragLeave={handleDrag}
      onDragOver={handleDrag}
      onDrop={handleDrop}
      onClick={() => fileInputRef.current?.click()}
    >
      <input 
        ref={fileInputRef}
        type="file" 
        style={{display: 'none'}} 
        accept="image/jpeg,image/png,image/webp,video/mp4,video/quicktime"
        onChange={handleChange}
      />
      
      <div className="upload-icon">📸</div>
      <h3>Drag & Drop your photo or video here</h3>
      <p style={{marginTop: '12px', fontSize: '0.9rem'}}>
        Supports JPG, PNG, WEBP images up to {config?.max_image_size_mb || 10}MB.<br/>
        For best results, ensure your full body is visible in the frame.
      </p>
      
      <button className="btn btn-secondary" style={{marginTop: '24px'}}>
        Browse Files
      </button>
    </div>
  );
}
