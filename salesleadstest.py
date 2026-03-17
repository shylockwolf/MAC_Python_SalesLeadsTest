import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox
import PyPDF2
import os
import requests
import json
import threading
from dotenv import load_dotenv

# 加载环境变量 - 使用脚本所在目录的.env文件
script_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(script_dir, '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)
    print(f"已加载环境变量文件: {env_path}")
else:
    load_dotenv()
    print("使用默认路径加载环境变量")


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
        # 初始化按钮状态（检查场景生成文件是否存在）
        self.update_button_states()
    
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
        
        self.scene_button = tk.Button(button_frame, text="场景生成", command=self.start_scene_generation_thread,
                                  bg="black", fg="gray", font=("Arial", 12), state=tk.DISABLED)
        self.scene_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.business_button = tk.Button(button_frame, text="商业目标", command=self.start_business_goal_thread,
                                  bg="black", fg="gray", font=("Arial", 12), state=tk.DISABLED)
        self.business_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.market_button = tk.Button(button_frame, text="目标市场锁定", command=self.start_market_target_thread,
                                  bg="black", fg="gray", font=("Arial", 12), state=tk.DISABLED)
        self.market_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.customer_button = tk.Button(button_frame, text="客户画像", command=self.start_customer_persona_thread,
                                  bg="black", fg="gray", font=("Arial", 12), state=tk.DISABLED)
        self.customer_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.customer_list_button = tk.Button(button_frame, text="客户列表", command=self.start_customer_list_thread,
                                  bg="black", fg="gray", font=("Arial", 12), state=tk.DISABLED)
        self.customer_list_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.info_label = tk.Label(button_frame, text="未打开文件", font=("Arial", 10))
        self.info_label.pack(side=tk.LEFT)
        
        debug_frame = tk.LabelFrame(main_frame, text="调试窗口（支持滚轮回滚、鼠标选中复制）", font=("Arial", 11, "bold"))
        debug_frame.pack(fill=tk.BOTH, expand=True)
        
        self.debug_text = scrolledtext.ScrolledText(debug_frame, wrap=tk.WORD, 
                                                    font=("Courier New", 10),
                                                    state=tk.NORMAL)
        self.debug_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 绑定右键菜单
        self.debug_text.bind("<Button-3>", self.show_context_menu)
        self.debug_text.bind("<Control-c>", self.copy_selection)
        self.debug_text.bind("<Command-c>", self.copy_selection)  # Mac快捷键
        
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
            individual_results = []
            
            # 步骤1: 依次为每个PDF文件调用DeepSeek API提取结构化信息
            self.root.after(0, lambda: self.debug_text.insert(tk.END, f"\n{'='*60}\n"))
            self.root.after(0, lambda: self.debug_text.insert(tk.END, "步骤1: 依次为每个PDF提取结构化产品信息\n"))
            self.root.after(0, lambda: self.debug_text.insert(tk.END, f"{'='*60}\n"))
            self.root.after(0, lambda: self.debug_text.see(tk.END))
            
            for i, content in enumerate(self.pdf_content):
                file_name = self.pdf_files[i]['file_name']
                
                self.root.after(0, lambda fn=file_name: self.debug_text.insert(tk.END, f"\n>>> 正在处理: {fn}\n"))
                self.root.after(0, lambda: self.debug_text.see(tk.END))
                
                # 调用API提取单个文件的结构化信息
                result = self.call_deepseek_api(content)
                
                if result:
                    individual_results.append(result)
                    self.extracted_results.append({
                        'file_name': file_name,
                        'extracted_data': result
                    })
                    
                    # 输出到调试窗口
                    self.root.after(0, lambda r=result, fn=file_name: self.debug_text.insert(tk.END, f"\n[{fn}] 提取结果:\n{r}\n"))
                    self.root.after(0, lambda: self.debug_text.insert(tk.END, "-" * 50 + "\n"))
                    self.root.after(0, lambda: self.debug_text.see(tk.END))
                else:
                    self.root.after(0, lambda fn=file_name: self.debug_text.insert(tk.END, f"\n[{fn}] 提取失败\n"))
                    self.root.after(0, lambda: self.debug_text.see(tk.END))
            
            # 步骤2: 合并所有结构化产品信息
            self.root.after(0, lambda: self.debug_text.insert(tk.END, f"\n{'='*60}\n"))
            self.root.after(0, lambda: self.debug_text.insert(tk.END, "步骤2: 合并所有结构化产品信息\n"))
            self.root.after(0, lambda: self.debug_text.insert(tk.END, f"{'='*60}\n"))
            self.root.after(0, lambda: self.debug_text.see(tk.END))
            
            merged_structured_text = "\n\n".join(individual_results)
            
            self.root.after(0, lambda: self.debug_text.insert(tk.END, f"合并完成，共 {len(individual_results)} 个文件的结构化信息\n"))
            self.root.after(0, lambda: self.debug_text.insert(tk.END, f"合并后文本长度: {len(merged_structured_text)} 字符\n"))
            self.root.after(0, lambda: self.debug_text.see(tk.END))
            
            # 步骤3: 对合并后的文本再次调用DeepSeek API提取结构化产品信息
            self.root.after(0, lambda: self.debug_text.insert(tk.END, f"\n{'='*60}\n"))
            self.root.after(0, lambda: self.debug_text.insert(tk.END, "步骤3: 对合并文本进行最终结构化提取\n"))
            self.root.after(0, lambda: self.debug_text.insert(tk.END, f"{'='*60}\n"))
            self.root.after(0, lambda: self.debug_text.see(tk.END))
            
            final_result = self.call_deepseek_api(merged_structured_text)
            
            if final_result:
                self.root.after(0, lambda r=final_result: self.debug_text.insert(tk.END, f"\n[最终提取结果]:\n{r}\n"))
                self.root.after(0, lambda: self.debug_text.insert(tk.END, "=" * 60 + "\n"))
                self.root.after(0, lambda: self.debug_text.see(tk.END))
                
                # 步骤4: 保存最终结果
                self.root.after(0, lambda: self.save_json_result(final_result))
            else:
                self.root.after(0, lambda: self.debug_text.insert(tk.END, "最终提取失败\n"))
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
                "model": "deepseek-reasoner",
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 128000
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
    
    def show_context_menu(self, event):
        """显示右键菜单"""
        context_menu = tk.Menu(self.root, tearoff=0)
        context_menu.add_command(label="复制", command=self.copy_selection)
        context_menu.add_command(label="复制全部", command=self.copy_all_content)
        context_menu.add_separator()
        context_menu.add_command(label="清空", command=self.clear_debug)
        context_menu.post(event.x_root, event.y_root)
    
    def copy_selection(self, event=None):
        """复制选中的文本"""
        try:
            selected = self.debug_text.selection_get()
            if selected:
                self.root.clipboard_clear()
                self.root.clipboard_append(selected)
        except tk.TclError:
            pass  # 没有选中文本
        return "break"
    
    def copy_all_content(self):
        """复制调试窗口全部内容"""
        content = self.debug_text.get(1.0, tk.END).strip()
        self.root.clipboard_clear()
        self.root.clipboard_append(content)
        messagebox.showinfo("成功", "全部内容已复制到剪贴板")
    
    def copy_content(self):
        """复制按钮功能"""
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
        
        # 检查是否存在产品抽取结果文件
        has_extract_result = os.path.exists("1.产品抽取结果.txt")
        
        # 检查是否存在场景文件
        has_scene_result = os.path.exists("2.模型推导场景.txt")
        
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
        
        # 场景生成按钮：只要有产品抽取结果文件就可以点击
        if has_extract_result:
            self.scene_button.config(state=tk.NORMAL, fg="blue")
        else:
            self.scene_button.config(state=tk.DISABLED, fg="gray")
        
        # 商业目标按钮：只要有场景文件就可以点击
        if has_scene_result:
            self.business_button.config(state=tk.NORMAL, fg="blue")
        else:
            self.business_button.config(state=tk.DISABLED, fg="gray")
        
        # 检查是否存在商业目标文件
        has_business_result = os.path.exists("3.模型推导商业目标.txt")
        
        # 目标市场锁定按钮：只要有商业目标文件就可以点击
        if has_business_result:
            self.market_button.config(state=tk.NORMAL, fg="blue")
        else:
            self.market_button.config(state=tk.DISABLED, fg="gray")
        
        # 检查是否存在目标市场锁定文件
        has_market_result = os.path.exists("4.目标市场锁定.txt")
        
        # 客户画像按钮：只要有目标市场锁定文件就可以点击
        if has_market_result:
            self.customer_button.config(state=tk.NORMAL, fg="blue")
        else:
            self.customer_button.config(state=tk.DISABLED, fg="gray")
        
        # 检查是否存在客户画像文件
        has_customer_result = os.path.exists("5.客户画像.txt")
        
        # 客户列表按钮：只要有客户画像文件就可以点击
        if has_customer_result:
            self.customer_list_button.config(state=tk.NORMAL, fg="blue")
        else:
            self.customer_list_button.config(state=tk.DISABLED, fg="gray")
    
    def save_json_result(self, result):
        try:
            json_start = result.find('{')
            json_end = result.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_str = result[json_start:json_end]
            else:
                json_str = result
            
            output_file = "1.产品抽取结果.txt"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(json_str)
            
            self.root.after(0, lambda: self.debug_text.insert(tk.END, f"\n结果已保存到: {output_file}\n"))
            self.root.after(0, lambda: self.debug_text.see(tk.END))
            
            # 更新按钮状态，启用场景生成按钮
            self.root.after(0, self.update_button_states)
            
            self.root.after(0, lambda: messagebox.showinfo("完成", 
                f"数据提取完成！\nJSON抽取结果已保存到: {output_file}"))
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("错误", f"保存结果时出错:\n{str(e)}"))
    
    def start_scene_generation_thread(self):
        """启动场景生成线程"""
        thread = threading.Thread(target=self.generate_scene)
        thread.daemon = True
        thread.start()
        
        self.debug_text.insert(tk.END, "\n开始场景生成...\n")
        self.debug_text.see(tk.END)
    
    def generate_scene(self):
        """场景生成功能：读取产品抽取结果和提示词，调用API生成场景"""
        try:
            # 步骤1: 读取产品抽取结果文件
            self.root.after(0, lambda: self.debug_text.insert(tk.END, "\n>>> 正在读取产品抽取结果...\n"))
            self.root.after(0, lambda: self.debug_text.see(tk.END))
            
            result_file = "1.产品抽取结果.txt"
            if not os.path.exists(result_file):
                self.root.after(0, lambda: messagebox.showerror("错误", f"找不到文件: {result_file}"))
                return
            
            with open(result_file, 'r', encoding='utf-8') as f:
                product_data = f.read()
            
            self.root.after(0, lambda: self.debug_text.insert(tk.END, f"成功读取产品抽取结果，长度: {len(product_data)} 字符\n"))
            self.root.after(0, lambda: self.debug_text.see(tk.END))
            
            # 步骤2: 读取场景生成提示词文件
            self.root.after(0, lambda: self.debug_text.insert(tk.END, ">>> 正在读取场景生成提示词...\n"))
            self.root.after(0, lambda: self.debug_text.see(tk.END))
            
            prompt_file = "p2.0 模型推导场景.txt"
            if not os.path.exists(prompt_file):
                self.root.after(0, lambda: messagebox.showerror("错误", f"找不到提示词文件: {prompt_file}"))
                return
            
            with open(prompt_file, 'r', encoding='utf-8') as f:
                scene_prompt = f.read()
            
            self.root.after(0, lambda: self.debug_text.insert(tk.END, f"成功读取场景生成提示词\n"))
            self.root.after(0, lambda: self.debug_text.see(tk.END))
            
            # 步骤3: 调用DeepSeek API生成场景
            self.root.after(0, lambda: self.debug_text.insert(tk.END, f"\n{'='*60}\n"))
            self.root.after(0, lambda: self.debug_text.insert(tk.END, "正在调用DeepSeek API生成场景...\n"))
            self.root.after(0, lambda: self.debug_text.insert(tk.END, f"{'='*60}\n"))
            self.root.after(0, lambda: self.debug_text.see(tk.END))
            
            result = self.call_deepseek_api_with_prompt(scene_prompt, product_data)
            
            if result:
                # 输出到调试窗口
                self.root.after(0, lambda r=result: self.debug_text.insert(tk.END, f"\n[场景生成结果]:\n{r}\n"))
                self.root.after(0, lambda: self.debug_text.insert(tk.END, "=" * 60 + "\n"))
                self.root.after(0, lambda: self.debug_text.see(tk.END))
                
                # 步骤4: 保存结果到文件
                self.save_scene_result(result)
            else:
                self.root.after(0, lambda: self.debug_text.insert(tk.END, "场景生成失败\n"))
                self.root.after(0, lambda: self.debug_text.see(tk.END))
                
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("错误", f"场景生成时出错:\n{str(e)}"))
    
    def call_deepseek_api_with_prompt(self, prompt_content, data_content):
        """调用DeepSeek API，使用指定的提示词和数据"""
        try:
            api_key = os.getenv("DEEPSEEK_API_KEY", "")
            if not api_key:
                return "错误: 未设置DeepSeek API密钥，请设置环境变量 DEEPSEEK_API_KEY"
            
            url = "https://api.deepseek.com/v1/chat/completions"
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
            
            # 构建提示词：提示词 + 产品数据
            full_prompt = f"{prompt_content}\n\n产品数据:\n{data_content}"
            
            data = {
                "model": "deepseek-reasoner",
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": full_prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 128000
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=120)
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                return f"API调用失败: {response.status_code} - {response.text}"
                
        except Exception as e:
            return f"API调用出错: {str(e)}"
    
    def save_scene_result(self, result):
        """保存场景生成结果到文件"""
        try:
            output_file = "2.模型推导场景.txt"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(result)
            
            self.root.after(0, lambda: self.debug_text.insert(tk.END, f"\n场景生成结果已保存到: {output_file}\n"))
            self.root.after(0, lambda: self.debug_text.see(tk.END))
            
            # 更新按钮状态，启用商业目标按钮
            self.root.after(0, self.update_button_states)
            
            self.root.after(0, lambda: messagebox.showinfo("完成", 
                f"场景生成完成！\n结果已保存到: {output_file}"))
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("错误", f"保存场景结果时出错:\n{str(e)}"))
    
    def start_business_goal_thread(self):
        """启动商业目标生成线程"""
        thread = threading.Thread(target=self.generate_business_goal)
        thread.daemon = True
        thread.start()
        
        self.debug_text.insert(tk.END, "\n开始商业目标生成...\n")
        self.debug_text.see(tk.END)
    
    def generate_business_goal(self):
        """商业目标生成功能：读取场景文件和提示词，调用API生成商业目标"""
        try:
            # 步骤1: 读取场景文件
            self.root.after(0, lambda: self.debug_text.insert(tk.END, "\n>>> 正在读取场景数据...\n"))
            self.root.after(0, lambda: self.debug_text.see(tk.END))
            
            scene_file = "2.模型推导场景.txt"
            if not os.path.exists(scene_file):
                self.root.after(0, lambda: messagebox.showerror("错误", f"找不到文件: {scene_file}"))
                return
            
            with open(scene_file, 'r', encoding='utf-8') as f:
                scene_data = f.read()
            
            self.root.after(0, lambda: self.debug_text.insert(tk.END, f"成功读取场景数据，长度: {len(scene_data)} 字符\n"))
            self.root.after(0, lambda: self.debug_text.see(tk.END))
            
            # 步骤2: 读取商业目标提示词文件
            self.root.after(0, lambda: self.debug_text.insert(tk.END, ">>> 正在读取商业目标提示词...\n"))
            self.root.after(0, lambda: self.debug_text.see(tk.END))
            
            prompt_file = "p3.0 模型推导商业目标.txt"
            if not os.path.exists(prompt_file):
                self.root.after(0, lambda: messagebox.showerror("错误", f"找不到提示词文件: {prompt_file}"))
                return
            
            with open(prompt_file, 'r', encoding='utf-8') as f:
                business_prompt = f.read()
            
            self.root.after(0, lambda: self.debug_text.insert(tk.END, f"成功读取商业目标提示词\n"))
            self.root.after(0, lambda: self.debug_text.see(tk.END))
            
            # 步骤3: 调用DeepSeek API生成商业目标
            self.root.after(0, lambda: self.debug_text.insert(tk.END, f"\n{'='*60}\n"))
            self.root.after(0, lambda: self.debug_text.insert(tk.END, "正在调用DeepSeek API生成商业目标...\n"))
            self.root.after(0, lambda: self.debug_text.insert(tk.END, f"{'='*60}\n"))
            self.root.after(0, lambda: self.debug_text.see(tk.END))
            
            result = self.call_deepseek_api_with_prompt(business_prompt, scene_data)
            
            if result:
                # 输出到调试窗口
                self.root.after(0, lambda r=result: self.debug_text.insert(tk.END, f"\n[商业目标生成结果]:\n{r}\n"))
                self.root.after(0, lambda: self.debug_text.insert(tk.END, "=" * 60 + "\n"))
                self.root.after(0, lambda: self.debug_text.see(tk.END))
                
                # 步骤4: 保存结果到文件
                self.save_business_goal_result(result)
            else:
                self.root.after(0, lambda: self.debug_text.insert(tk.END, "商业目标生成失败\n"))
                self.root.after(0, lambda: self.debug_text.see(tk.END))
                
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("错误", f"商业目标生成时出错:\n{str(e)}"))
    
    def save_business_goal_result(self, result):
        """保存商业目标生成结果到文件"""
        try:
            output_file = "3.模型推导商业目标.txt"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(result)
            
            self.root.after(0, lambda: self.debug_text.insert(tk.END, f"\n商业目标生成结果已保存到: {output_file}\n"))
            self.root.after(0, lambda: self.debug_text.see(tk.END))
            
            # 更新按钮状态，启用目标市场锁定按钮
            self.root.after(0, self.update_button_states)
            
            self.root.after(0, lambda: messagebox.showinfo("完成", 
                f"商业目标生成完成！\n结果已保存到: {output_file}"))
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("错误", f"保存商业目标结果时出错:\n{str(e)}"))
    
    def start_market_target_thread(self):
        """启动目标市场锁定线程"""
        thread = threading.Thread(target=self.generate_market_target)
        thread.daemon = True
        thread.start()
        
        self.debug_text.insert(tk.END, "\n开始目标市场锁定...\n")
        self.debug_text.see(tk.END)
    
    def generate_market_target(self):
        """目标市场锁定功能：读取商业目标文件和提示词，调用API生成目标市场锁定"""
        try:
            # 步骤1: 读取商业目标文件
            self.root.after(0, lambda: self.debug_text.insert(tk.END, "\n>>> 正在读取商业目标数据...\n"))
            self.root.after(0, lambda: self.debug_text.see(tk.END))
            
            business_file = "3.模型推导商业目标.txt"
            if not os.path.exists(business_file):
                self.root.after(0, lambda: messagebox.showerror("错误", f"找不到文件: {business_file}"))
                return
            
            with open(business_file, 'r', encoding='utf-8') as f:
                business_data = f.read()
            
            self.root.after(0, lambda: self.debug_text.insert(tk.END, f"成功读取商业目标数据，长度: {len(business_data)} 字符\n"))
            self.root.after(0, lambda: self.debug_text.see(tk.END))
            
            # 步骤2: 读取目标市场锁定提示词文件
            self.root.after(0, lambda: self.debug_text.insert(tk.END, ">>> 正在读取目标市场锁定提示词...\n"))
            self.root.after(0, lambda: self.debug_text.see(tk.END))
            
            prompt_file = "p4.0 目标市场锁定.txt"
            if not os.path.exists(prompt_file):
                self.root.after(0, lambda: messagebox.showerror("错误", f"找不到提示词文件: {prompt_file}"))
                return
            
            with open(prompt_file, 'r', encoding='utf-8') as f:
                market_prompt = f.read()
            
            self.root.after(0, lambda: self.debug_text.insert(tk.END, f"成功读取目标市场锁定提示词\n"))
            self.root.after(0, lambda: self.debug_text.see(tk.END))
            
            # 步骤3: 调用DeepSeek API生成目标市场锁定
            self.root.after(0, lambda: self.debug_text.insert(tk.END, f"\n{'='*60}\n"))
            self.root.after(0, lambda: self.debug_text.insert(tk.END, "正在调用DeepSeek API生成目标市场锁定...\n"))
            self.root.after(0, lambda: self.debug_text.insert(tk.END, f"{'='*60}\n"))
            self.root.after(0, lambda: self.debug_text.see(tk.END))
            
            result = self.call_deepseek_api_with_prompt(market_prompt, business_data)
            
            if result:
                # 输出到调试窗口
                self.root.after(0, lambda r=result: self.debug_text.insert(tk.END, f"\n[目标市场锁定生成结果]:\n{r}\n"))
                self.root.after(0, lambda: self.debug_text.insert(tk.END, "=" * 60 + "\n"))
                self.root.after(0, lambda: self.debug_text.see(tk.END))
                
                # 步骤4: 保存结果到文件
                self.save_market_target_result(result)
            else:
                self.root.after(0, lambda: self.debug_text.insert(tk.END, "目标市场锁定生成失败\n"))
                self.root.after(0, lambda: self.debug_text.see(tk.END))
                
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("错误", f"目标市场锁定生成时出错:\n{str(e)}"))
    
    def save_market_target_result(self, result):
        """保存目标市场锁定生成结果到文件"""
        try:
            output_file = "4.目标市场锁定.txt"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(result)
            
            self.root.after(0, lambda: self.debug_text.insert(tk.END, f"\n目标市场锁定生成结果已保存到: {output_file}\n"))
            self.root.after(0, lambda: self.debug_text.see(tk.END))
            
            # 更新按钮状态，启用客户画像按钮
            self.root.after(0, self.update_button_states)
            
            self.root.after(0, lambda: messagebox.showinfo("完成", 
                f"目标市场锁定生成完成！\n结果已保存到: {output_file}"))
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("错误", f"保存目标市场锁定结果时出错:\n{str(e)}"))
    
    def start_customer_persona_thread(self):
        """启动客户画像线程"""
        thread = threading.Thread(target=self.generate_customer_persona)
        thread.daemon = True
        thread.start()
        
        self.debug_text.insert(tk.END, "\n开始客户画像生成...\n")
        self.debug_text.see(tk.END)
    
    def generate_customer_persona(self):
        """客户画像功能：读取目标市场锁定文件和提示词，调用API生成客户画像"""
        try:
            # 步骤1: 读取目标市场锁定文件
            self.root.after(0, lambda: self.debug_text.insert(tk.END, "\n>>> 正在读取目标市场锁定数据...\n"))
            self.root.after(0, lambda: self.debug_text.see(tk.END))
            
            market_file = "4.目标市场锁定.txt"
            if not os.path.exists(market_file):
                self.root.after(0, lambda: messagebox.showerror("错误", f"找不到文件: {market_file}"))
                return
            
            with open(market_file, 'r', encoding='utf-8') as f:
                market_data = f.read()
            
            self.root.after(0, lambda: self.debug_text.insert(tk.END, f"成功读取目标市场锁定数据，长度: {len(market_data)} 字符\n"))
            self.root.after(0, lambda: self.debug_text.see(tk.END))
            
            # 步骤2: 读取客户画像提示词文件
            self.root.after(0, lambda: self.debug_text.insert(tk.END, ">>> 正在读取客户画像提示词...\n"))
            self.root.after(0, lambda: self.debug_text.see(tk.END))
            
            prompt_file = "p5.0 客户画像.txt"
            if not os.path.exists(prompt_file):
                self.root.after(0, lambda: messagebox.showerror("错误", f"找不到提示词文件: {prompt_file}"))
                return
            
            with open(prompt_file, 'r', encoding='utf-8') as f:
                customer_prompt = f.read()
            
            self.root.after(0, lambda: self.debug_text.insert(tk.END, f"成功读取客户画像提示词\n"))
            self.root.after(0, lambda: self.debug_text.see(tk.END))
            
            # 步骤3: 调用DeepSeek API生成客户画像
            self.root.after(0, lambda: self.debug_text.insert(tk.END, f"\n{'='*60}\n"))
            self.root.after(0, lambda: self.debug_text.insert(tk.END, "正在调用DeepSeek API生成客户画像...\n"))
            self.root.after(0, lambda: self.debug_text.insert(tk.END, f"{'='*60}\n"))
            self.root.after(0, lambda: self.debug_text.see(tk.END))
            
            result = self.call_deepseek_api_with_prompt(customer_prompt, market_data)
            
            if result:
                # 输出到调试窗口
                self.root.after(0, lambda r=result: self.debug_text.insert(tk.END, f"\n[客户画像生成结果]:\n{r}\n"))
                self.root.after(0, lambda: self.debug_text.insert(tk.END, "=" * 60 + "\n"))
                self.root.after(0, lambda: self.debug_text.see(tk.END))
                
                # 步骤4: 保存结果到文件
                self.save_customer_persona_result(result)
            else:
                self.root.after(0, lambda: self.debug_text.insert(tk.END, "客户画像生成失败\n"))
                self.root.after(0, lambda: self.debug_text.see(tk.END))
                
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("错误", f"客户画像生成时出错:\n{str(e)}"))
    
    def save_customer_persona_result(self, result):
        """保存客户画像生成结果到文件"""
        try:
            output_file = "5.客户画像.txt"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(result)
            
            self.root.after(0, lambda: self.debug_text.insert(tk.END, f"\n客户画像生成结果已保存到: {output_file}\n"))
            self.root.after(0, lambda: self.debug_text.see(tk.END))
            
            self.root.after(0, lambda: messagebox.showinfo("完成", 
                f"客户画像生成完成！\n结果已保存到: {output_file}"))
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("错误", f"保存客户画像结果时出错:\n{str(e)}"))
    
    def start_customer_list_thread(self):
        """启动客户列表生成线程"""
        thread = threading.Thread(target=self.generate_customer_list)
        thread.daemon = True
        thread.start()
        
        self.debug_text.insert(tk.END, "\n开始客户列表生成...\n")
        self.debug_text.see(tk.END)
    
    def generate_customer_list(self):
        """客户列表生成功能：读取客户画像文件和提示词，调用API生成客户列表"""
        try:
            # 步骤1: 读取客户画像文件
            self.root.after(0, lambda: self.debug_text.insert(tk.END, "\n>>> 正在读取客户画像数据...\n"))
            self.root.after(0, lambda: self.debug_text.see(tk.END))
            
            customer_file = "5.客户画像.txt"
            if not os.path.exists(customer_file):
                self.root.after(0, lambda: messagebox.showerror("错误", f"找不到文件: {customer_file}"))
                return
            
            with open(customer_file, 'r', encoding='utf-8') as f:
                customer_data = f.read()
            
            self.root.after(0, lambda: self.debug_text.insert(tk.END, f"成功读取客户画像数据，长度: {len(customer_data)} 字符\n"))
            self.root.after(0, lambda: self.debug_text.see(tk.END))
            
            # 步骤2: 读取客户列表提示词文件
            self.root.after(0, lambda: self.debug_text.insert(tk.END, ">>> 正在读取客户列表提示词...\n"))
            self.root.after(0, lambda: self.debug_text.see(tk.END))
            
            prompt_file = "p6.0 客户列表.txt"
            if not os.path.exists(prompt_file):
                self.root.after(0, lambda: messagebox.showerror("错误", f"找不到提示词文件: {prompt_file}"))
                return
            
            with open(prompt_file, 'r', encoding='utf-8') as f:
                customer_list_prompt = f.read()
            
            self.root.after(0, lambda: self.debug_text.insert(tk.END, f"成功读取客户列表提示词\n"))
            self.root.after(0, lambda: self.debug_text.see(tk.END))
            
            # 步骤3: 调用DeepSeek API生成客户列表
            self.root.after(0, lambda: self.debug_text.insert(tk.END, f"\n{'='*60}\n"))
            self.root.after(0, lambda: self.debug_text.insert(tk.END, "正在调用DeepSeek API生成客户列表...\n"))
            self.root.after(0, lambda: self.debug_text.insert(tk.END, f"{'='*60}\n"))
            self.root.after(0, lambda: self.debug_text.see(tk.END))
            
            result = self.call_deepseek_api_with_prompt(customer_list_prompt, customer_data)
            
            if result:
                # 输出到调试窗口
                self.root.after(0, lambda r=result: self.debug_text.insert(tk.END, f"\n[客户列表生成结果]:\n{r}\n"))
                self.root.after(0, lambda: self.debug_text.insert(tk.END, "=" * 60 + "\n"))
                self.root.after(0, lambda: self.debug_text.see(tk.END))
                
                # 步骤4: 保存结果到文件
                self.save_customer_list_result(result)
            else:
                self.root.after(0, lambda: self.debug_text.insert(tk.END, "客户列表生成失败\n"))
                self.root.after(0, lambda: self.debug_text.see(tk.END))
                
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("错误", f"客户列表生成时出错:\n{str(e)}"))
    
    def save_customer_list_result(self, result):
        """保存客户列表生成结果到文件"""
        try:
            output_file = "6.客户列表.txt"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(result)
            
            self.root.after(0, lambda: self.debug_text.insert(tk.END, f"\n客户列表生成结果已保存到: {output_file}\n"))
            self.root.after(0, lambda: self.debug_text.see(tk.END))
            
            self.root.after(0, lambda: messagebox.showinfo("完成", 
                f"客户列表生成完成！\n结果已保存到: {output_file}"))
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("错误", f"保存客户列表结果时出错:\n{str(e)}"))


if __name__ == "__main__":
    root = tk.Tk()
    app = SalesLeadsTestApp(root)
    root.mainloop()
