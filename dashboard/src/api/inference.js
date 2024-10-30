const API_BASE_URL = process.env.REACT_APP_API_BASE_URL;


export async function originalFileUpload(file) {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE_URL}/inference/upload`, {
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


export async function generateInferenceFile({ originalFileName, modelName }) {
    const response = await fetch(`${API_BASE_URL}/inference/generate`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
            original_file_name: originalFileName,
            m_name: modelName
        })
    });

    if (response.ok) {
        const data = await response.json(); 
        return data;
    } else {
        throw new Error(response.statusText);
    }
}


export async function deleteOriginalFile(originalFileName) {
    const response = await fetch(`${API_BASE_URL}/inference/${originalFileName}`, {
        method: 'DELETE'
    });

    if (response.ok) {
        return true;
    } else {
        throw new Error(response.statusText);
    }
}


export async function getModelList() {
    const response = await fetch(`${API_BASE_URL}/inference/list`);
    
    if (response.ok) {
        const list = await response.json();
        return list;
    } else {
        throw new Error(response.statusText);
    }
}


export async function getModelStatus() {
    const response = await fetch(`${API_BASE_URL}/inference/status`);
    
    if (response.ok) {
        const list = await response.json();
        return list;
    } else {
        throw new Error(response.statusText);
    }
}