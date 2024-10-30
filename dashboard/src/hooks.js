import { useRef, useEffect, useCallback } from 'react';

export function useExecuteRepeat() {
    const isRunningRef = useRef(false); 
    const timeoutIdRef = useRef(null); 

    const executeLogic = useCallback(async (logicToExecute, interval) => {
        try {
            await logicToExecute(); // 비동기 로직 실행
            if (isRunningRef.current) {
                timeoutIdRef.current = setTimeout(() => executeLogic(logicToExecute, interval), interval); // 재귀적으로 실행
            }
        } catch (error) {
            console.error("작업 중 예외 발생:", error);
            clearTimeout(timeoutIdRef.current); // 예외 발생 시 타이머 중단
            timeoutIdRef.current = null;
            isRunningRef.current = false; // 상태 초기화
        }
    }, []);

    const executeRepeat = useCallback(async (logicToExecute, interval = 1000) => {
        if (isRunningRef.current) {
            return;
        }

        isRunningRef.current = true; 
        executeLogic(logicToExecute, interval); // 첫 실행과 이후 반복을 동일하게 처리
    }, [executeLogic]);

    const stopExecution = useCallback(() => {
        if (timeoutIdRef.current) {
            clearTimeout(timeoutIdRef.current); // 타이머 중단
            timeoutIdRef.current = null;
            isRunningRef.current = false; // 상태 초기화
        }
    }, []);

    // 컴포넌트 언마운트 시 정리
    useEffect(() => {
        return () => {
            stopExecution(); // 컴포넌트 언마운트 시 실행 중단
        };
    }, [stopExecution]);

    return { executeRepeat, stopExecution };
}
