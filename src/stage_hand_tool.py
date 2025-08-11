import subprocess
import json
import tempfile
import os
import sys

def browser_automation(task_description: str, website_url: str) -> str:
    """Run browser automation in a separate process to avoid threading issues."""
    
    # Create a temporary script to run browser automation
    script_content = f'''
import os
import asyncio
import sys
import json
import nest_asyncio
from stagehand import Stagehand, StagehandConfig

# Disable CrewAI telemetry
os.environ["OTEL_SDK_DISABLED"] = "true"
nest_asyncio.apply()

async def main():
    stagehand = None
    try:
        api_key = "{os.getenv("OPENAI_API_KEY", "")}"
        base_url = "{os.getenv("OPENAI_API_BASE", "https://llmfoundry.straive.com/openai/v1/")}"
        
        if not api_key:
            result = {{"success": False, "data": "", "error": "OPENAI_API_KEY not set"}}
            print(json.dumps(result))
            return
        
        config = StagehandConfig(
            env="LOCAL",
            model_name="gpt-4o",
            self_heal=True,
            system_prompt="You are a browser automation assistant that extracts specific information accurately.",
            model_client_options={{
                "apiKey": api_key,
                "baseURL": base_url
            }},
            verbose=1,
        )
        
        stagehand = Stagehand(config)
        await stagehand.init()
        await stagehand.page.goto("{website_url}")
        
        # Use page.act instead of extract to avoid schema issues
        enhanced_instruction = """
{task_description}

Instructions:
1. Navigate to relevant sections if needed
2. Extract specific data requested
3. Provide precise information, not summaries and its most importnat part
4. Focus on factual data extraction
5. Return the exact information found
"""
        
        # Use act method which is more reliable
        result = await stagehand.page.act(enhanced_instruction)
        
        if result:
            response = {{
                "success": True, 
                "data": str(result),
                "error": ""
            }}
        else:
            response = {{
                "success": False,
                "data": "",
                "error": "No data could be extracted from the page"
            }}
        
        print(json.dumps(response))
        
    except Exception as e:
        error_response = {{
            "success": False,
            "data": "",
            "error": str(e)
        }}
        print(json.dumps(error_response))
    
    finally:
        if stagehand:
            try:
                await stagehand.close()
            except Exception as cleanup_error:
                pass

if __name__ == "__main__":
    asyncio.run(main())
'''
    
    try:
        # Write script to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
            f.write(script_content)
            script_path = f.name
        
        # Get the Python executable from current environment
        python_executable = sys.executable
        
        # Run the script in a subprocess
        result = subprocess.run(
            [python_executable, script_path],
            capture_output=True,
            text=True,
            timeout=180,  # 3 minute timeout
            env=os.environ.copy()  # Pass environment variables
        )
        
        # Clean up temp file
        try:
            os.unlink(script_path)
        except:
            pass
        
        if result.returncode == 0 and result.stdout.strip():
            try:
                response = json.loads(result.stdout.strip())
                if response['success']:
                    return f"Browser Automation Success:\\n{response['data']}"
                else:
                    return f"Browser Automation Failed: {response['error']}"
            except json.JSONDecodeError:
                return f"Browser Automation Output: {result.stdout.strip()}"
        else:
            error_msg = result.stderr or f"Process exited with code {result.returncode}"
            return f"Process Error: {error_msg}"
            
    except subprocess.TimeoutExpired:
        try:
            os.unlink(script_path)
        except:
            pass
        return "Error: Browser automation timed out after 3 minutes"
    except Exception as e:
        return f"Subprocess Error: {str(e)}"
