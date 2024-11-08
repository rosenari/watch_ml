const API_BASE_URL = process.env.REACT_APP_API_BASE_URL;


export async function datasetUpload(file) {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE_URL}/dataset/upload`, {
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


export async function getDatasetList() {
    const response = await fetch(`${API_BASE_URL}/dataset/list`);
    
    if (response.ok) {
        const list = await response.json();
        return list;
    } else {
        throw new Error(response.statusText);
    }
}


export async function deleteDataset(datasetId) {
    const response = await fetch(`${API_BASE_URL}/dataset/${datasetId}`, {
        method: 'DELETE'
    });

    if (response.ok) {
        return true;
    } else {
        throw new Error(response.statusText);
    }
}


export async function validDataset(datasetIds) {
    const requests = datasetIds.map(datasetId => 
        fetch(`${API_BASE_URL}/dataset/validation`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ dataset_id: datasetId })
        })
    );

    const responses = await Promise.all(requests);

    const results = await Promise.all(responses.map(async (response) => {
        if (!response.ok) {
            throw new Error(`파일 유효성 검증 요청 실패: ${response.status} ${response.statusText}`);
        }

        const data = await response.json();

        if (data.result !== true) {
            throw new Error(`파일 유효성 검증 요청 실패: ${JSON.stringify(data)}`);
        }

        return data;
    }));

    return results;
}


export async function getDatasetStatus() {
    const response = await fetch(`${API_BASE_URL}/dataset/status`);
    if (response.ok) {
        const list = await response.json();
        return list;
    } else {
        throw new Error(response.statusText);
    }
}