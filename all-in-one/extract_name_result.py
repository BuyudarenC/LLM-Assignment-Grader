import json

input_file = "./deepseek_grading_results.jsonl"
output_file = "./demo.jsonl"

with open(input_file, "r", encoding="utf-8") as fin, open(output_file, "w", encoding="utf-8") as fout:
    for line in fin:
        data = json.loads(line)
        out = {
            "student_name": data.get("student_name"),
            "grading_result": data.get("grading_result")
        }
        fout.write(json.dumps(out, ensure_ascii=False) + "\n")

print("提取完成，结果已保存到", output_file)