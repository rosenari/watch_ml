export async function fileUpload(file) {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch('http://localhost:5000/files/upload', {
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
    const response = await fetch('http://localhost:5000/files/list');
    
    if (response.ok) {
        const list = await response.json();
        return list;
    } else {
        throw new Error(response.statusText);
    }
}

export async function deleteFile(fileName) {
    const response = await fetch(`http://localhost:5000/files/${fileName}`, {
        method: 'DELETE'
    });

    if (response.ok) {
        return true;
    } else {
        throw new Error(response.statusText);
    }
}

export async function validFiles(fileNames) {
    const requests = fileNames.map(fileName => 
        fetch(`http://localhost:5000/files/validation`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ file_name: fileName })
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

export async function getValidFiles() {
    const response = await fetch(`http://localhost:5000/files/validation`);
    if (response.ok) {
        const list = await response.json();
        return list;
    } else {
        throw new Error(response.statusText);
    }
}