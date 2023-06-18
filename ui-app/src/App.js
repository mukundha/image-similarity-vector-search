import React, { useRef, useState, useEffect } from 'react';
import axios from 'axios';
import Webcam from 'react-webcam';
import './App.css'; // Import the CSS file here

const ProductCard = ({ product }) => {
  return (
    <div className="card">
      <img src={product.image_id} alt={product.item_name} />
      <h3>{product.item_name}</h3>
    </div>
  );
};

function App() {
  const webcamRef = useRef(null);
  const [products, setProducts] = useState([]);

  const capturePhoto = async () => {
    if (webcamRef.current) {
      const photoData = webcamRef.current.getScreenshot();

      try {
        const response = await axios.post('<api-server>/upload', { photoData });
        setProducts(response.data);
      } catch (error) {
        console.error(error);
      }
    }
  };

  useEffect(() => {
    // Access the media devices and select the back camera
    navigator.mediaDevices.enumerateDevices()
      .then(devices => {
        const videoDevices = devices.filter(device => device.kind === 'videoinput');
        const backCamera = videoDevices.find(device => device.label.toLowerCase().includes('back'));
        
        if (backCamera) {
          const constraints = { deviceId: { exact: backCamera.deviceId } };
          webcamRef.current.video.srcObject.getVideoTracks().forEach(track => track.stop());
          webcamRef.current.video.srcObject = null;
          navigator.mediaDevices.getUserMedia({ video: constraints })
            .then(stream => {
              webcamRef.current.video.srcObject = stream;
            })
            .catch(error => {
              console.error('Error accessing back camera:', error);
            });
        }
      })
      .catch(error => {
        console.error('Error enumerating media devices:', error);
      });
  }, []);

  return (
    <div>
      <button className="capture-button" onClick={capturePhoto}>Capture Photo</button>
      <Webcam ref={webcamRef} screenshotFormat="image/jpeg" videoConstraints={{ facingMode: 'environment' }} />

      <div className="product-list">
        {products.map((product, index) => (
          <ProductCard key={index} product={product} />
        ))}
      </div>
    </div>
  );
}

export default App;
