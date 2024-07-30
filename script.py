import csv
import os
import re
import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
import pandas as pd
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import json
from datetime import datetime
import logging
class AdvancedCSVSearchTool(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Advanced CSV Search Tool")
        self.geometry("1000x800")
        logging.basicConfig(filename='csv_search_tool.log', level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s')
        self.create_widgets()
    def create_widgets(self):
        # Directory selection
        self.dir_frame = ctk.CTkFrame(self)
        self.dir_frame.pack(pady=10, padx=10, fill="x")
        self.dir_label = ctk.CTkLabel(self.dir_frame, text="Directory:")
        self.dir_label.pack(side="left", padx=(0, 10))
        self.dir_entry = ctk.CTkEntry(self.dir_frame, width=300)
        self.dir_entry.pack(side="left", expand=True, fill="x")
        self.dir_button = ctk.CTkButton(self.dir_frame, text="Browse", command=self.browse_directory)
        self.dir_button.pack(side="right", padx=(10, 0))
        # Search criteria
        self.criteria_frame = ctk.CTkFrame(self)
        self.criteria_frame.pack(pady=10, padx=10, fill="x")
        self.column_label = ctk.CTkLabel(self.criteria_frame, text="Column:")
        self.column_label.pack(side="left", padx=(0, 10))
        self.column_entry = ctk.CTkEntry(self.criteria_frame, width=150)
        self.column_entry.pack(side="left", expand=True, fill="x")
        self.value_label = ctk.CTkLabel(self.criteria_frame, text="Value:")
        self.value_label.pack(side="left", padx=(10, 10))
        self.value_entry = ctk.CTkEntry(self.criteria_frame, width=150)
        self.value_entry.pack(side="left", expand=True, fill="x")
        # Advanced search options
        self.advanced_frame = ctk.CTkFrame(self)
        self.advanced_frame.pack(pady=10, padx=10, fill="x")
        self.case_sensitive_var = ctk.BooleanVar()
        self.case_sensitive_check = ctk.CTkCheckBox(self.advanced_frame, text="Case Sensitive", variable=self.case_sensitive_var)
        self.case_sensitive_check.pack(side="left", padx=(0, 10))
        self.regex_var = ctk.BooleanVar()
        self.regex_check = ctk.CTkCheckBox(self.advanced_frame, text="Use Regex", variable=self.regex_var)
        self.regex_check.pack(side="left", padx=(0, 10))
        self.date_frame = ctk.CTkFrame(self.advanced_frame)
        self.date_frame.pack(side="left", padx=(0, 10))
        self.start_date_label = ctk.CTkLabel(self.date_frame, text="Start Date:")
        self.start_date_label.pack(side="left")
        self.start_date_entry = ctk.CTkEntry(self.date_frame, width=100)
        self.start_date_entry.pack(side="left")
        self.end_date_label = ctk.CTkLabel(self.date_frame, text="End Date:")
        self.end_date_label.pack(side="left")
        self.end_date_entry = ctk.CTkEntry(self.date_frame, width=100)
        self.end_date_entry.pack(side="left")
        # Export options
        self.export_frame = ctk.CTkFrame(self)
        self.export_frame.pack(pady=10, padx=10, fill="x")
        self.export_format_label = ctk.CTkLabel(self.export_frame, text="Export Format:")
        self.export_format_label.pack(side="left")
        self.export_format_var = ctk.StringVar(value="CSV")
        self.export_format_menu = ctk.CTkOptionMenu(self.export_frame, variable=self.export_format_var, values=["CSV", "Excel", "JSON"])
        self.export_format_menu.pack(side="left", padx=(10, 0))
        # Search and save/load buttons
        self.button_frame = ctk.CTkFrame(self)
        self.button_frame.pack(pady=10, padx=10, fill="x")
        self.search_button = ctk.CTkButton(self.button_frame, text="Search", command=self.perform_search)
        self.search_button.pack(side="left", padx=(0, 10))
        self.save_criteria_button = ctk.CTkButton(self.button_frame, text="Save Criteria", command=self.save_search_criteria)
        self.save_criteria_button.pack(side="left", padx=(0, 10))
        self.load_criteria_button = ctk.CTkButton(self.button_frame, text="Load Criteria", command=self.load_search_criteria)
        self.load_criteria_button.pack(side="left")
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(self)
        self.progress_bar.pack(pady=10, padx=10, fill="x")
        self.progress_bar.set(0)
        # Results display
        self.results_text = ctk.CTkTextbox(self, height=200)
        self.results_text.pack(pady=10, padx=10, expand=True, fill="both")
        # Data visualization
        self.figure = Figure(figsize=(5, 4), dpi=100)
        self.plot = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, master=self)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(pady=10, padx=10, expand=True, fill="both")
    def browse_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.dir_entry.delete(0, "end")
            self.dir_entry.insert(0, directory)
    def perform_search(self):
        try:
            directory = self.dir_entry.get()
            column = self.column_entry.get()
            value = self.value_entry.get()
            case_sensitive = self.case_sensitive_var.get()
            use_regex = self.regex_var.get()
            start_date = self.start_date_entry.get()
            end_date = self.end_date_entry.get()
            if not directory or not column or not value:
                raise ValueError("Please provide a directory, column name, and search value.")
            self.results_text.delete("1.0", "end")
            self.progress_bar.set(0)
            self.search_thread = threading.Thread(target=self.search_worker, args=(directory, column, value, case_sensitive, use_regex, start_date, end_date))
            self.search_thread.start()
        except Exception as e:
            self.show_error(f"Error starting search: {str(e)}")
            logging.error(f"Error in perform_search: {str(e)}", exc_info=True)
    def search_worker(self, directory, column, value, case_sensitive, use_regex, start_date, end_date):
        try:
            matching_rows = []
            total_files = len([f for f in os.listdir(directory) if f.endswith('.csv')])
            processed_files = 0
            for filename in os.listdir(directory):
                if filename.endswith('.csv'):
                    filepath = os.path.join(directory, filename)
                    self.update_results(f"Processing file: {filepath}\n")
                    df = pd.read_csv(filepath)
                    if column not in df.columns:
                        self.update_results(f"Column '{column}' not found in {filename}, skipping...\n")
                        continue
                    mask = self.create_search_mask(df, column, value, case_sensitive, use_regex)
                    if start_date and end_date:
                        date_mask = (df['date'] >= start_date) & (df['date'] <= end_date)
                        mask = mask & date_mask
                    matching_rows.extend(df[mask].to_dict('records'))
                    processed_files += 1
                    self.update_progress(processed_files / total_files)
            if matching_rows:
                self.save_results(matching_rows)
                self.update_results(f"Found {len(matching_rows)} matching records.\n")
                self.visualize_data(matching_rows)
            else:
                self.update_results("No matching records found.\n")
        except Exception as e:
            self.show_error(f"Error during search: {str(e)}")
            logging.error(f"Error in search_worker: {str(e)}", exc_info=True)
    def create_search_mask(self, df, column, value, case_sensitive, use_regex):
        if use_regex:
            if case_sensitive:
                return df[column].str.contains(value, regex=True, na=False)
            else:
                return df[column].str.contains(value, regex=True, case=False, na=False)
        else:
            if case_sensitive:
                return df[column] == value
            else:
                return df[column].str.lower() == value.lower()
    def update_results(self, message):
        self.results_text.insert("end", message)
        self.results_text.see("end")
        self.update_idletasks()
    def update_progress(self, progress):
        self.progress_bar.set(progress)
        self.update_idletasks()
    def save_results(self, matching_rows):
        try:
            export_format = self.export_format_var.get()
            if export_format == "CSV":
                self.save_csv(matching_rows)
            elif export_format == "Excel":
                self.save_excel(matching_rows)
            elif export_format == "JSON":
                self.save_json(matching_rows)
        except Exception as e:
            self.show_error(f"Error saving results: {str(e)}")
            logging.error(f"Error in save_results: {str(e)}", exc_info=True)
    def save_csv(self, matching_rows):
        csv_file = 'matching_records.csv'
        pd.DataFrame(matching_rows).to_csv(csv_file, index=False)
        self.update_results(f"CSV file saved to: {csv_file}\n")
    def save_excel(self, matching_rows):
        excel_file = 'matching_records.xlsx'
        pd.DataFrame(matching_rows).to_excel(excel_file, index=False)
        self.update_results(f"Excel file saved to: {excel_file}\n")
    def save_json(self, matching_rows):
        json_file = 'matching_records.json'
        with open(json_file, mode='w', encoding='utf-8') as output_json:
            json.dump(matching_rows, output_json, indent=2)
        self.update_results(f"JSON file saved to: {json_file}\n")
    def visualize_data(self, matching_rows):
        try:
            df = pd.DataFrame(matching_rows)
            numeric_columns = df.select_dtypes(include=[np.number]).columns
            if not numeric_columns.empty:
                column_to_plot = numeric_columns[0]  # Choose the first numeric column
                df['index'] = range(len(df))
                self.plot.clear()
                self.plot.plot(df['index'], df[column_to_plot])
                self.plot.set_title(f'{column_to_plot} for Matching Records')
                self.plot.set_xlabel('Record Index')
                self.plot.set_ylabel(column_to_plot)
                self.figure.tight_layout()
                self.canvas.draw()
            else:
                self.update_results("No numeric data available for visualization.\n")
        except Exception as e:
            self.show_error(f"Error visualizing data: {str(e)}")
            logging.error(f"Error in visualize_data: {str(e)}", exc_info=True)
    def save_search_criteria(self):
        try:
            criteria = {
                'directory': self.dir_entry.get(),
                'column': self.column_entry.get(),
                'value': self.value_entry.get(),
                'case_sensitive': self.case_sensitive_var.get(),
                'use_regex': self.regex_var.get(),
                'start_date': self.start_date_entry.get(),
                'end_date': self.end_date_entry.get(),
                'export_format': self.export_format_var.get()
            }
            file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
            if file_path:
                with open(file_path, 'w') as f:
                    json.dump(criteria, f)
                self.update_results(f"Search criteria saved to: {file_path}\n")
        except Exception as e:
            self.show_error(f"Error saving search criteria: {str(e)}")
            logging.error(f"Error in save_search_criteria: {str(e)}", exc_info=True)
    def load_search_criteria(self):
        try:
            file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
            if file_path:
                with open(file_path, 'r') as f:
                    criteria = json.load(f)
                self.dir_entry.delete(0, "end")
                self.dir_entry.insert(0, criteria.get('directory', ''))
                self.column_entry.delete(0, "end")
                self.column_entry.insert(0, criteria.get('column', ''))
                self.value_entry.delete(0, "end")
                self.value_entry.insert(0, criteria.get('value', ''))
                self.case_sensitive_var.set(criteria.get('case_sensitive', False))
                self.regex_var.set(criteria.get('use_regex', False))
                self.start_date_entry.delete(0, "end")
                self.start_date_entry.insert(0, criteria.get('start_date', ''))
                self.end_date_entry.delete(0, "end")
                self.end_date_entry.insert(0, criteria.get('end_date', ''))
                self.export_format_var.set(criteria.get('export_format', 'CSV'))
                self.update_results(f"Search criteria loaded from: {file_path}\n")
        except Exception as e:
            self.show_error(f"Error loading search criteria: {str(e)}")
            logging.error(f"Error in load_search_criteria: {str(e)}", exc_info=True)
    def show_error(self, message):
        messagebox.showerror("Error", message)
        self.update_results(f"Error: {message}\n")
        logging.error(message)
def main():
    try:
        app = AdvancedCSVSearchTool()
        app.mainloop()
    except Exception as e:
        logging.critical(f"Critical error in main application: {str(e)}", exc_info=True)
        messagebox.showerror("Critical Error", f"An unexpected error occurred: {str(e)}\nPlease check the log file for details.")
if __name__ == "__main__":
    main()