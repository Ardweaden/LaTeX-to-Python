# -*- coding: utf-8 -*-
"""
Created on Thu Aug  8 17:20:33 2019

@author: Jan Jezersek
"""
import re
import sys
    
class LaTeX:
    def __init__(self,filename):
        with open(filename,'r') as f:
            self.latexfile = f.readlines()
        
        self.filename = ".".join(filename.split(".")[:-1])
        self.exec_string = ""
        self.used_indices = {}
        self.indent = 0
        self.check_end = []

        self.patterns = {
                "import": {
                        "pattern": "\\\\usepackage{(.*)}",
                        "groups": [1],
                        "instructions": None,
                        "python_code": "import {}\n",
                        "indent": 0,
                        },
                "import_as": {
                        "pattern": "\\\\usepackage\[(.*)\]{(.*)}",
                        "groups": [2,1],
                        "instructions": None,
                        "python_code": "import {} as {}\n",
                        "indent": 0,
                        },
                "for": {
                        "pattern": "\\\\begin{for}",
                        "groups": [1],
                        "instructions":["NEXT LINE"],
                        "python_code": "for {}:\n",
                        "indent": 4,
                        }, 
                "for_end": {
                        "pattern": "\\\\end{for}",
                        "groups": [],
                        "instructions": None,
                        "python_code": "\r\n",
                        "indent": -4,
                        },
                "while": {
                        "pattern": "\\\\begin{while}",
                        "groups": [1],
                        "instructions":["NEXT LINE"],
                        "python_code": "while {}:\n",
                        "indent": 4,
                        }, 
                "while_end": {
                        "pattern": "\\\\end{while}",
                        "groups": [],
                        "instructions": None,
                        "python_code": "\r\n",
                        "indent": -4,
                        },
                "set_variable": {
                        "pattern": "\\\\newcommand{(.*)}{(.*)}",
                        "groups": [1,2],
                        "instructions": None,
                        "python_code": "{} = {}\n",
                        "indent": 0,
                        },
                "counter": {
                        "pattern": "\\\\addtocounter{(.*)}{(.*)}",
                        "groups": [1,2],
                        "instructions": None,
                        "python_code": "{} += {}\n",
                        "indent": 0,
                        },
                "set_loop_condition": {
                        "pattern": "\\\\newcommand{(.*)}\[(in|<|=<|<=|=>|>=|>)\]{(.*)}",
                        "groups": [1,2,3],
                        "instructions": None,
                        "python_code": "{} {} {}",
                        "indent": 0,
                        },
                "print": {
                        "pattern": "\\\\textup{(.*)}",
                        "groups": [1],
                        "instructions": None,
                        "python_code": "print(\'{}\')\n",
                        "indent": 0,
                        },
                "mathmode_oneline": {
                        "pattern": "\$\$(.*)\$\$",
                        "groups": [1],
                        "instructions": None,
                        "python_code": "{}\n",
                        "indent": 0,
                        },
                "mathmode_multiline": {
                        "pattern": "\$\$(.*)",
                        "groups": [1],
                        "instructions": ["UNTIL (.*)\$\$","SET_CHECK_END"],
                        "python_code": "{}\n",
                        "indent": 0,
                        },
                "class": {
                        "pattern": "\\\\documentclass{(.*)}",
                        "groups": [1],
                        "instructions": ["SET_CHECK_END","SET_VALUES"],
                        "python_code": "class {}:\n",
                        "indent": 4,
                        },
                "class_inheritance": {
                        "pattern": "\\\\documentclass\[(.*)\]{(.*)}",
                        "groups": [2,1],
                        "instructions": ["SET_CHECK_END","SET_VALUES"],
                        "python_code": "class {}({}):\n",
                        "indent": 4,
                        },
                "end_check": {
                        "pattern": "^\n$",
                        "groups": [],
                        "instructions": ["CHECK_END"],
                        "python_code": "\r\n",
                        "indent": 0,
                        },
                "function": {
                        "pattern": "\\\\section\[(.*)\]{(.*)}",
                        "groups": [2,1],
                        "instructions": ["SET_CHECK_END","SET_VALUES"],
                        "python_code": "def {}({}):\n",
                        "indent": 4,
                        },
            }
    
    def line_parse(self,line,index):
        line=line.replace("\t","")
        
        for key in self.patterns.keys():
            matches = re.search(self.patterns[key]["pattern"],line)
            
            if matches:
                groups = self.patterns[key]["groups"]
                instructions = self.patterns[key]["instructions"]
                self.indent += self.patterns[key]["indent"]
                
                if instructions:
                    values = []
                    
                    for instruction in instructions:
                        if instruction == "NEXT LINE":
                            values.append(self.line_parse(self.latexfile[index+1],index+1))
                            self.used_indices[index+1] = True
                            
                        if instruction == "SET_CHECK_END":
                            self.check_end.append(True)
                            
                        if instruction.split(" ")[0] == "UNTIL":
                            code_string = matches.group(1)+"\n"
                            count = index+1
                            while count < len(self.latexfile):
                                matches_end = re.search(instruction.split(" ")[1],self.latexfile[count])
                                self.used_indices[count] = True
                                if matches_end:
                                    code_string += matches_end.group(1)
                                    values.append(code_string)
                                    break
                                code_string += self.latexfile[count]
                                count += 1
                                
                        if instruction == "CHECK_END":
                            if self.check_end:
                                del self.check_end[-1]
                                self.indent = 0
                            else:
                                continue
                            
                        if instruction == "SET_VALUES":
                            values = [matches.group(i) for i in groups]
                else:      
                    values = [matches.group(i) for i in groups]
                    
                code = self.patterns[key]["python_code"].format(*values)
                    
                return code
        print(line,"didn't match any patterns")
        return ''
    
    def parse_file(self):
        for index,line in enumerate(self.latexfile):
            try:
                self.used_indices[index]
            except:
                indent_string = self.indent * " "
                code = self.line_parse(line,index)
                self.exec_string += indent_string + code
                
    def execute(self):
        exec(self.exec_string)
                
    def save(self,filename=None):         
        if filename is None:
            filename = self.filename + ".py"
        
        with open(filename,"w") as f:
            f.write(self.exec_string)
    
if __name__ == "__main__":
    filename = sys.argv[1]
    l=LaTeX(filename)
    l.parse_file()
    l.execute()
    l.save()