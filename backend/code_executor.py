import subprocess
import os
import tempfile
from typing import Dict, Optional


class CodeExecutor:
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
    
    def execute(self, code: str, language: str = "python", stdin_input: str = None) -> Dict:
        """Execute code in the specified language, optionally piping stdin_input."""
        language = language.lower().strip()

        if language in ["python", "py"]:
            return self._execute_python(code, stdin_input)
        elif language in ["javascript", "js"]:
            return self._execute_javascript(code, stdin_input)
        elif language == "java":
            return self._execute_java(code, stdin_input)
        elif language in ["cpp", "c++"]:
            return self._execute_cpp(code, stdin_input)
        else:
            return {
                "success": False,
                "error": f"Unsupported language: {language}"
            }

    def execute_with_test_case(self, code: str, language: str, input_data: str, expected_output: str) -> Dict:
        """
        Execute code with given stdin input and compare output with expected.
        Returns result with pass/fail, actual output, etc.
        """
        result = self.execute(code, language, stdin_input=input_data)

        if not result.get("success"):
            return {
                "passed": False,
                "actual_output": result.get("error", ""),
                "expected_output": expected_output.strip(),
                "error": result.get("error", "Execution failed"),
                "status": "Runtime Error" if "timeout" not in result.get("error", "").lower() else "Time Limit Exceeded"
            }

        actual = result.get("output", "").strip()
        expected = expected_output.strip()

        passed = actual == expected

        return {
            "passed": passed,
            "actual_output": actual,
            "expected_output": expected,
            "error": None,
            "status": "Accepted" if passed else "Wrong Answer"
        }

    def _execute_python(self, code: str, stdin_input: str = None) -> Dict:
        """Execute Python code"""
        try:
            result = subprocess.run(
                ["python", "-c", code],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                input=stdin_input
            )

            if result.returncode == 0:
                return {
                    "success": True,
                    "output": result.stdout if result.stdout else "(No output)"
                }
            else:
                return {
                    "success": False,
                    "error": result.stderr if result.stderr else "Unknown error"
                }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": f"Code execution timeout (>{self.timeout}s)"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def _execute_javascript(self, code: str, stdin_input: str = None) -> Dict:
        """Execute JavaScript code using Node.js"""
        try:
            result = subprocess.run(
                ["node", "-e", code],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                input=stdin_input
            )

            if result.returncode == 0:
                return {
                    "success": True,
                    "output": result.stdout if result.stdout else "(No output)"
                }
            else:
                return {
                    "success": False,
                    "error": result.stderr if result.stderr else "Unknown error"
                }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": f"Code execution timeout (>{self.timeout}s)"
            }
        except FileNotFoundError:
            return {
                "success": False,
                "error": "Node.js not installed. Install Node.js to run JavaScript"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def _execute_java(self, code: str, stdin_input: str = None) -> Dict:
        """Execute Java code"""
        try:
            # Create temp directory
            with tempfile.TemporaryDirectory() as tmpdir:
                # Write Java file
                java_file = os.path.join(tmpdir, "Main.java")
                with open(java_file, "w") as f:
                    f.write(code)

                # Compile
                compile_result = subprocess.run(
                    ["javac", java_file],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout
                )

                if compile_result.returncode != 0:
                    return {
                        "success": False,
                        "error": compile_result.stderr if compile_result.stderr else "Compilation error"
                    }

                # Run
                run_result = subprocess.run(
                    ["java", "-cp", tmpdir, "Main"],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                    input=stdin_input
                )

                if run_result.returncode == 0:
                    return {
                        "success": True,
                        "output": run_result.stdout if run_result.stdout else "(No output)"
                    }
                else:
                    return {
                        "success": False,
                        "error": run_result.stderr if run_result.stderr else "Runtime error"
                    }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": f"Code execution timeout (>{self.timeout}s)"
            }
        except FileNotFoundError:
            return {
                "success": False,
                "error": "Java not installed. Install JDK to run Java code"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def _execute_cpp(self, code: str, stdin_input: str = None) -> Dict:
        """Execute C++ code"""
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                # Write C++ file
                cpp_file = os.path.join(tmpdir, "main.cpp")
                exe_file = os.path.join(tmpdir, "main")

                with open(cpp_file, "w") as f:
                    f.write(code)

                # Compile
                compile_result = subprocess.run(
                    ["g++", cpp_file, "-o", exe_file],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout
                )

                if compile_result.returncode != 0:
                    return {
                        "success": False,
                        "error": compile_result.stderr if compile_result.stderr else "Compilation error"
                    }

                # Run
                run_result = subprocess.run(
                    [exe_file],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                    input=stdin_input
                )

                if run_result.returncode == 0:
                    return {
                        "success": True,
                        "output": run_result.stdout if run_result.stdout else "(No output)"
                    }
                else:
                    return {
                        "success": False,
                        "error": run_result.stderr if run_result.stderr else "Runtime error"
                    }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": f"Code execution timeout (>{self.timeout}s)"
            }
        except FileNotFoundError:
            return {
                "success": False,
                "error": "G++ not installed. Install GCC to run C++ code"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }