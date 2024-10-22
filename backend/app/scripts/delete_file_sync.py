"""
is_delete가 체크된 DataSet, AiModel, InferenceFile 제거
"""

import os
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from app.entity import DataSet, AiModel, InferenceFile, FileMeta
from app.database import get_session


async def delete_related_file_meta(file_meta: FileMeta, db: AsyncSession):
    if file_meta:
        if os.path.exists(file_meta.filepath):
            os.remove(file_meta.filepath)  
            print(f"Deleted file: {file_meta.filepath}")
        await db.delete(file_meta)  
        print(f"Deleted FileMeta record: {file_meta.filepath}")


async def delete_file_records_and_files(db: AsyncSession):
    result = await db.execute(
        select(DataSet)
        .filter(DataSet.is_delete == True)
        .options(joinedload(DataSet.file_meta))
    )
    datasets_to_delete = result.scalars().all()

    for dataset in datasets_to_delete:
        await delete_related_file_meta(dataset.file_meta, db)
        await db.delete(dataset)  
        print(f"Deleted DataSet record: {dataset.filename}")

    result = await db.execute(
        select(AiModel)
        .filter(AiModel.is_delete == True)
        .options(joinedload(AiModel.file_meta))
    )
    models_to_delete = result.scalars().all()

    for model in models_to_delete:
        await delete_related_file_meta(model.file_meta, db) 
        await db.delete(model) 
        print(f"Deleted AiModel record: {model.filename}")

    result = await db.execute(
        select(InferenceFile)
        .filter(InferenceFile.is_delete == True)
        .options(
            joinedload(InferenceFile.original_file),
            joinedload(InferenceFile.generated_file)
        )
    )
    inference_files_to_delete = result.scalars().all()

    for inference_file in inference_files_to_delete:
        await delete_related_file_meta(inference_file.original_file, db) 
        await delete_related_file_meta(inference_file.generated_file, db) 

        await db.delete(inference_file) 
        print(f"Deleted InferenceFile record: {inference_file.original_file_name}")

    await db.commit()


async def main():
    async for session in get_session():
        await delete_file_records_and_files(session)

if __name__ == "__main__":
    asyncio.run(main())
