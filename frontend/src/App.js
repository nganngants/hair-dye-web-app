import React, { useState } from 'react';
import './App.css';
function App() {
  const [selectedColor, setSelectedColor] = useState('');
  const [selectedImage, setSelectedImage] = useState(null);
  const [previewImage, setPreviewImage] = useState(null);
  const [dyedImage, setDyedImage] = useState(null);

  const handleColorChange = (event) => {
    setSelectedColor(event.target.value);
  };

  const handleImageChange = (event) => {
    const file = event.target.files[0];
    setSelectedImage(file);
    setPreviewImage(URL.createObjectURL(file));
  };

  const handleDyeClick = () => {
    if (!selectedColor || !selectedImage) {
      alert('Please select both a color and an image.');
      return;
    }

    const formData = new FormData();
    formData.append('color', selectedColor);
    formData.append('image', selectedImage);

    fetch('/dye', {
      method: 'POST',
      body: formData,
    })
      .then((response) => response.blob())
      .then((blob) => {
        const imageUrl = URL.createObjectURL(blob);
        setDyedImage(imageUrl);
      })
      .catch((error) => {
        console.error('Error:', error);
      });
  };

  return (
    <div className='App'>
      <h1>Hair Dye App</h1>
      <div className='setting'>
        <div className='selectColor'>
          <label className='custom-file'>
            Select Color
            <input
              type="color"
              value={selectedColor}
              onChange={handleColorChange}
              />
          </label>
        </div>
      </div>
      <div>
        <label className='selectImage'>
          Select Image
          <input type="file" accept="image/*" onChange={handleImageChange} />
        </label>
      </div>
      <div className='display'>
        {previewImage && (
          <div>
            <h2>Selected Image:</h2>
            <img src={previewImage} alt="Selected" style={{ maxWidth: '300px' }} />
          </div>
        )}
        {dyedImage && (
          <div>
            <h2>Dyed Image:</h2>
            <img src={dyedImage} alt="Dyed" style={{ maxWidth: '300px' }} />
          </div>
        )}
      </div>
      <button id='butDye' onClick={handleDyeClick}>Dye</button>
    </div>
  );
}

export default App;
