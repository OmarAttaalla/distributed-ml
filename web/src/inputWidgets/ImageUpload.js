import React, {useState} from "react";
import "./ImageUpload.css";


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

    return (
        <div className="fileUploadContainer">
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
        </div>
    );
}