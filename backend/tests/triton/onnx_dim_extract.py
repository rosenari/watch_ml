import onnx

def get_onnx_output_dims(onnx_model_path: str):
    try:
        model = onnx.load(onnx_model_path)
        output_dims = []
        for output in model.graph.output:
            dims = [dim.dim_value if dim.dim_value > 0 else -1 for dim in output.type.tensor_type.shape.dim]
            output_dims.append(dims)
        return output_dims
    except Exception as e:
        print(f"Error extracting ONNX output dimensions: {e}")
        return None
    

if __name__ == '__main__':
    print(get_onnx_output_dims('../../mlruns/triton_repo/example_model/9/model.onnx'))