import React, {useState} from "react";
import "./ImageUpload.css";

import downloadImage from "../images/download-black.png";


export default function ImageUpload() {
    const [fileName, setFileName] = useState("No image selected");

    function handleFileChange(event) {
        const files = event.target.files;

        console.log(files);

        if (files.length === 1) {
            setFileName(files[0].name);
        } else if (files.length > 1) {
            setFileName(`${files.length} images selected`);
        } else {
            setFileName("No image selected");
        }
    }

    function handleDragOver(event) {
        event.preventDefault();
        event.dataTransfer.dropEffect = 'copy';
        document.getElementsByClassName('fileUploadContainer')[0].classList.add('fileUploadContainerDrag');
        console.log('drag over');
    }

    function handleDrop(event) {
        event.preventDefault();
        document.getElementsByClassName('fileUploadContainer')[0].classList.remove('fileUploadContainerDrag');

        var files = event.dataTransfer.files;
        console.log(files);
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
                <button className="uploadButton">Upload</button>
            </div>
            <div className="dropImageContainer">
                <img src={downloadImage} alt="" className="uploadImage" />
                Drop images here
            </div>
        </div>
    );
}