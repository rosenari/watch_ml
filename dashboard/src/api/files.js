export async function fileUpload(file) {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch('http://localhost:8000/files/upload', {
        method: 'POST',
        body: formData,
    });

    if (response.ok) {
        const data = await response.json();  // 텍스트로 응답 데이터 추출
        return data;
    } else {
        throw new Error(response.statusText);
    }
}

export async function getFileList() {
    const response = await fetch('http://localhost:8000/files/list');
    
    if (response.ok) {
        const list = await response.json();
        return list;
    } else {
        throw new Error(response.statusText);
    }
}

export async function deleteFile(fileName) {
    const response = await fetch(`http://localhost:8000/files/${fileName}`, {
        method: 'DELETE'
    });

    if (response.ok) {
        return true;
    } else {
        throw new Error(response.statusText);
    }
}