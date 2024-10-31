import { atom } from 'jotai';

export const state = { dataset: [], model: [], inference: [] };
export const modelAtom = atom([]);
export const datasetAtom = atom([]); 
export const inferenceAtom = atom([]);