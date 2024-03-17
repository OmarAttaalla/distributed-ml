import React, { useState } from "react";
import "./ImageUpload.css";
import axios from "axios";

import downloadImage from "../images/download-black.png";

export default function ImageUpload() {
    const [fileName, setFileName] = useState("No image selected");

    function handleFileChange(event) {
        const files = event.target.files;
        updateFileName(files);
    }

    function handleDragOver(event) {
        event.preventDefault();
        event.dataTransfer.dropEffect = 'copy';
        document.getElementsByClassName('fileUploadContainer')[0].classList.add('fileUploadContainerDrag');
    }

    function handleDrop(event) {
        event.preventDefault();
        document.getElementsByClassName('fileUploadContainer')[0].classList.remove('fileUploadContainerDrag');

        const files = event.dataTransfer.files;
        updateFileName(files);

        const fileList = new DataTransfer();
        Array.from(files).forEach(file => {
            fileList.items.add(file);
        });

        const fileInput = document.getElementsByClassName('inputFile')[0];
        fileInput.files = fileList.files;
        fileInput.dispatchEvent(new Event('change'));
    }

    function updateFileName(files) {
        if (files.length === 1) {
            setFileName(files[0].name);
        } else if (files.length > 1) {
            setFileName(`${files.length} images selected`);
        } else {
            setFileName("No image selected");
        }
    }

    function uploadImages() {
        const files = document.getElementsByClassName('inputFile')[0].files;
        const formData = new FormData();

        for (let i = 0; i < files.length; i++) {
            formData.append('file', files[i]);
        }

        axios.post('http://127.0.0.1:5000/upload', formData, {
            headers: {
                'Content-Type': 'multipart/form-data'
            }
        }).then(response => {
            console.log(response);
        }).catch(error => {
            console.log(error);
        });
    }

    return (
        <div className="fileUploadContainer" onDragOver={handleDragOver} onDrop={handleDrop}>
            <div className="fileUploadButtonContainer">
                <label className="fileLabel">
                    <input
                        type="file"
                        accept="image/*"
                        onChange={handleFileChange}
                        className="inputFile"
                        multiple="multiple"
                    />
                    Upload Image
                </label>
                <div className="fileName">{fileName}</div>
                <button className="uploadButton" onClick={uploadImages}>Upload</button>
            </div>
            <div className="dropImageContainer">
                <img src={downloadImage} alt="" className="uploadImage" />
                Drop images here
            </div>
        </div>
    );
}
