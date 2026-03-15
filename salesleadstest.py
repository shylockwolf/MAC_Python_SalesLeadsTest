import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox
import PyPDF2
import os
import requests
import json
import threading
from dotenv import load_dotenv

load_dotenv()


class SalesLeadsTestApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SalesLeadsTest - PDF解析器")
        self.root.geometry("1000x700")
        
        self.pdf_files = []
        self.pdf_content = []
        self.extracted_results = []
        self.current_index = 0
        self.prompt_content = ""
        
        self.load_prompt()
        self.create_widgets()
    
    def load_prompt(self):
        try:
            prompt_file = "p1.0 提取产品信息.txt"
            if os.path.exists(prompt_file):
                with open(prompt_file, 'r', encoding='utf-8') as f:
                    self.prompt_content = f.read()
                print(f"成功加载提示词文件: {prompt_file}")
            else:
                self.prompt_content = "请从以下PDF内容中提取产品信息。"
                print(f"提示词文件不存在，使用默认提示词")
        except Exception as e:
            self.prompt_content = "请从以下PDF内容中提取产品信息。"
            print(f"加载提示词文件失败: {str(e)}")
    
    def create_widgets(self):
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        button_frame = tk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.open_button = tk.Button(button_frame, text="打开PDF文件", command=self.open_pdf, 
                               bg="black", fg="blue", font=("Arial", 12))
        self.open_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.extract_button = tk.Button(button_frame, text="DeepSeek提取", command=self.start_extraction_thread,
                                  bg="black", fg="gray", font=("Arial", 12), state=tk.DISABLED)
        self.extract_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.info_label = tk.Label(button_frame, text="未打开文件", font=("Arial", 10))
        self.info_label.pack(side=tk.LEFT)
        
        debug_frame = tk.LabelFrame(main_frame, text="调试窗口", font=("Arial", 11, "bold"))
        debug_frame.pack(fill=tk.BOTH, expand=True)
        
        self.debug_text = scrolledtext.ScrolledText(debug_frame, wrap=tk.WORD, 
                                                    font=("Courier New", 10))
        self.debug_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        control_frame = tk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.prev_button = tk.Button(control_frame, text="上一条", command=self.prev_content,
                               bg="black", fg="gray", font=("Arial", 10), state=tk.DISABLED)
        self.prev_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.next_button = tk.Button(control_frame, text="下一条", command=self.next_content,
                               bg="black", fg="gray", font=("Arial", 10), state=tk.DISABLED)
        self.next_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.copy_button = tk.Button(control_frame, text="复制当前内容", command=self.copy_content,
                               bg="black", fg="gray", font=("Arial", 10), state=tk.DISABLED)
        self.copy_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.clear_button = tk.Button(control_frame, text="清空调试窗口", command=self.clear_debug,
                               bg="black", fg="blue", font=("Arial", 10))
        self.clear_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.index_label = tk.Label(control_frame, text="", font=("Arial", 10))
        self.index_label.pack(side=tk.RIGHT)
    
    def open_pdf(self):
        file_paths = filedialog.askopenfilenames(
            title="选择PDF文件（可多选）",
            filetypes=[("PDF文件", "*.pdf"), ("所有文件", "*.*")]
        )
        
        if file_paths:
            self.parse_pdfs(file_paths)
    
    def parse_pdfs(self, file_paths):
        try:
            self.pdf_files = []
            self.pdf_content = []
            self.extracted_results = []
            
            for file_path in file_paths:
                file_name = os.path.basename(file_path)
                
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    num_pages = len(pdf_reader.pages)
                    
                    full_text = ""
                    for page_num in range(num_pages):
                        page = pdf_reader.pages[page_num]
                        text = page.extract_text()
                        full_text += text + "\n"
                    
                    file_info = {
                        'file_name': file_name,
                        'file_path': file_path,
                        'num_pages': num_pages,
                        'content': full_text
                    }
                    self.pdf_files.append(file_info)
                    self.pdf_content.append(full_text)
                    
                    self.debug_text.insert(tk.END, f"文件名: {file_name}\n")
                    self.debug_text.insert(tk.END, f"页数: {num_pages}\n")
                    self.debug_text.insert(tk.END, "-" * 50 + "\n\n")
                    self.debug_text.see(tk.END)
            
            self.current_index = 0
            self.info_label.config(text=f"已打开 {len(self.pdf_files)} 个PDF文件")
            self.update_index_label()
            self.update_button_states()
            
            messagebox.showinfo("成功", f"PDF文件解析完成！\n共解析 {len(self.pdf_files)} 个文件。")
            
        except Exception as e:
            messagebox.showerror("错误", f"解析PDF文件时出错:\n{str(e)}")
    
    def start_extraction_thread(self):
        if not self.pdf_content:
            messagebox.showwarning("警告", "请先打开PDF文件")
            return
        
        thread = threading.Thread(target=self.extract_with_deepseek)
        thread.daemon = True
        thread.start()
        
        self.debug_text.insert(tk.END, "开始调用DeepSeek API进行数据提取...\n")
        self.debug_text.see(tk.END)
    
    def extract_with_deepseek(self):
        try:
            self.extracted_results = []
            
            self.root.after(0, lambda: self.debug_text.insert(tk.END, "\n正在合并所有PDF文本...\n"))
            self.root.after(0, lambda: self.debug_text.see(tk.END))
            
            merged_text = ""
            for i, content in enumerate(self.pdf_content):
                file_name = self.pdf_files[i]['file_name']
                merged_text += f"\n{'='*50}\n"
                merged_text += f"文件: {file_name}\n"
                merged_text += f"{'='*50}\n"
                merged_text += content + "\n"
            
            self.root.after(0, lambda: self.debug_text.insert(tk.END, f"合并完成，总文本长度: {len(merged_text)} 字符\n"))
            self.root.after(0, lambda: self.debug_text.see(tk.END))
            
            self.root.after(0, lambda: self.debug_text.insert(tk.END, "\n正在调用DeepSeek API进行JSON抽取...\n"))
            self.root.after(0, lambda: self.debug_text.see(tk.END))
            
            result = self.call_deepseek_api(merged_text)
            
            if result:
                self.extracted_results.append({
                    'file_name': '合并结果',
                    'extracted_data': result
                })
                
                self.root.after(0, lambda r=result: self.debug_text.insert(tk.END, f"\nJSON抽取结果:\n{r}\n"))
                self.root.after(0, lambda: self.debug_text.insert(tk.END, "=" * 50 + "\n"))
                self.root.after(0, lambda: self.debug_text.see(tk.END))
                
                self.root.after(0, lambda: self.save_json_result(result))
            else:
                self.root.after(0, lambda: self.debug_text.insert(tk.END, "JSON抽取失败\n"))
                self.root.after(0, lambda: self.debug_text.see(tk.END))
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("错误", f"提取数据时出错:\n{str(e)}"))
    
    def call_deepseek_api(self, pdf_content):
        try:
            api_key = os.getenv("DEEPSEEK_API_KEY", "")
            if not api_key:
                return "错误: 未设置DeepSeek API密钥，请设置环境变量 DEEPSEEK_API_KEY"
            
            url = "https://api.deepseek.com/v1/chat/completions"
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
            
            prompt = f"{self.prompt_content}\n\nPDF内容:\n{pdf_content}"
            
            data = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 2000
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                return f"API调用失败: {response.status_code} - {response.text}"
                
        except Exception as e:
            return f"API调用出错: {str(e)}"
    
    def prev_content(self):
        if not self.pdf_files:
            messagebox.showwarning("警告", "请先打开PDF文件")
            return
        
        if self.current_index > 0:
            self.current_index -= 1
            self.display_current_content()
    
    def next_content(self):
        if not self.pdf_files:
            messagebox.showwarning("警告", "请先打开PDF文件")
            return
        
        if self.current_index < len(self.pdf_files) - 1:
            self.current_index += 1
            self.display_current_content()
    
    def display_current_content(self):
        self.debug_text.delete(1.0, tk.END)
        file_info = self.pdf_files[self.current_index]
        self.debug_text.insert(tk.END, f"文件名: {file_info['file_name']}\n")
        self.debug_text.insert(tk.END, f"页数: {file_info['num_pages']}\n")
        self.debug_text.insert(tk.END, "-" * 50 + "\n")
        
        if self.extracted_results and self.current_index < len(self.extracted_results):
            self.debug_text.insert(tk.END, f"\n提取结果:\n{self.extracted_results[self.current_index]['extracted_data']}\n")
        
        self.update_index_label()
    
    def copy_content(self):
        if not self.pdf_files:
            messagebox.showwarning("警告", "没有内容可复制")
            return
        
        content = self.debug_text.get(1.0, tk.END).strip()
        self.root.clipboard_clear()
        self.root.clipboard_append(content)
        messagebox.showinfo("成功", "内容已复制到剪贴板")
    
    def clear_debug(self):
        self.debug_text.delete(1.0, tk.END)
        self.pdf_files = []
        self.pdf_content = []
        self.extracted_results = []
        self.current_index = 0
        self.info_label.config(text="未打开文件")
        self.update_index_label()
        self.update_button_states()
    
    def update_index_label(self):
        if self.pdf_files:
            self.index_label.config(text=f"当前: {self.current_index + 1} / {len(self.pdf_files)}")
        else:
            self.index_label.config(text="")
    
    def update_button_states(self):
        has_files = len(self.pdf_files) > 0
        
        if has_files:
            self.extract_button.config(state=tk.NORMAL, fg="blue")
            self.prev_button.config(state=tk.NORMAL, fg="blue")
            self.next_button.config(state=tk.NORMAL, fg="blue")
            self.copy_button.config(state=tk.NORMAL, fg="blue")
        else:
            self.extract_button.config(state=tk.DISABLED, fg="gray")
            self.prev_button.config(state=tk.DISABLED, fg="gray")
            self.next_button.config(state=tk.DISABLED, fg="gray")
            self.copy_button.config(state=tk.DISABLED, fg="gray")
    
    def save_json_result(self, result):
        try:
            json_start = result.find('{')
            json_end = result.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_str = result[json_start:json_end]
            else:
                json_str = result
            
            output_file = "产品抽取结果.txt"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(json_str)
            
            self.root.after(0, lambda: self.debug_text.insert(tk.END, f"\n结果已保存到: {output_file}\n"))
            self.root.after(0, lambda: self.debug_text.see(tk.END))
            
            self.root.after(0, lambda: messagebox.showinfo("完成", 
                f"数据提取完成！\nJSON抽取结果已保存到: {output_file}"))
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("错误", f"保存结果时出错:\n{str(e)}"))


if __name__ == "__main__":
    root = tk.Tk()
    app = SalesLeadsTestApp(root)
    root.mainloop()
