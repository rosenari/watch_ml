const API_BASE_URL = process.env.REACT_APP_API_BASE_URL;


export async function createModel({ modelName, baseModelName, zipFileNames = [], modelExt = 'pt'}) {
    const response = await fetch(`${API_BASE_URL}/ml/create`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
            m_name: modelName, 
            b_m_name: baseModelName, 
            zip_files: zipFileNames, 
            m_ext: modelExt 
        })
    });

    if (response.ok) {
        const data = await response.json();  // 텍스트로 응답 데이터 추출
        return data;
    } else {
        throw new Error(response.statusText);
    }
}


export async function deployModel({ modelName }) {
    const response = await fetch(`${API_BASE_URL}/ml/deploy`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
            m_name: modelName
        })
    });

    if (response.ok) {
        const data = await response.json();  // 텍스트로 응답 데이터 추출
        return data;
    } else {
        throw new Error(response.statusText);
    }
}


export async function undeployModel({ modelName }) {
    const response = await fetch(`${API_BASE_URL}/ml/undeploy`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
            m_name: modelName
        })
    });

    if (response.ok) {
        const data = await response.json();  // 텍스트로 응답 데이터 추출
        return data;
    } else {
        throw new Error(response.statusText);
    }
}


export async function getModelList() {
    const response = await fetch(`${API_BASE_URL}/ml/list`);
    
    if (response.ok) {
        const list = await response.json();
        return list;
    } else {
        throw new Error(response.statusText);
    }
}


export async function getModelStatus() {
    const response = await fetch(`${API_BASE_URL}/ml/status`);
    
    if (response.ok) {
        const list = await response.json();
        return list;
    } else {
        throw new Error(response.statusText);
    }
}