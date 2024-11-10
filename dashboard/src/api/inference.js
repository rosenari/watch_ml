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


export async function generateInferenceFile({ inferenceFileId, modelId }) {
    const response = await fetch(`${API_BASE_URL}/inference/generate`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
            inference_file_id: inferenceFileId,
            m_id: modelId
        })
    });

    if (response.ok) {
        const data = await response.json(); 
        return data;
    } else {
        throw new Error(response.statusText);
    }
}


export async function deleteOriginalFile(inferenceFileId) {
    const response = await fetch(`${API_BASE_URL}/inference/${inferenceFileId}`, {
        method: 'DELETE'
    });

    if (response.ok) {
        return true;
    } else {
        throw new Error(response.statusText);
    }
}


export async function getInferenceList(lastId = null) {
    const url = lastId !== null ? `${API_BASE_URL}/inference/list?last_id=${lastId}` : `${API_BASE_URL}/inference/list`;
    const response = await fetch(url);
    
    if (response.ok) {
        const list = await response.json();
        return list;
    } else {
        throw new Error(response.statusText);
    }
}


export async function getInferenceStatus() {
    const response = await fetch(`${API_BASE_URL}/inference/status`);
    
    if (response.ok) {
        const list = await response.json();
        return list;
    } else {
        throw new Error(response.statusText);
    }
}


export function downloadFileLink(fileId) {
    return `${API_BASE_URL}/inference/download/${fileId}`
}