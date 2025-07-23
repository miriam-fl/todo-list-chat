# agent_service.py
import json
import httpx
from todo_service import get_tasks, add_task, update_task, delete_task

# Define the system functions as JSON for GPT
FUNCTIONS_JSON = json.dumps({
    "functions": [
        {"name": "get_tasks", "description": "Get all tasks", "parameters": {}},
        {"name": "add_task", "description": "Add a new task", "parameters": {"task": "dict"}},
        {"name": "update_task", "description": "Update a task by id", "parameters": {"task_id": "str", "new_task": "dict"}},
        {"name": "delete_task", "description": "Delete a task by id", "parameters": {"task_id": "str"}}
    ]
})


async def agent(query):
    print(f"[DEBUG] Starting agent with query: {query}")
    
    headers = {
        "Authorization": f"Bearer sk-f3bdae3dd24420c96ed9ffbb661261889c6d9c65ee9efc57",
        "Content-Type": "application/json"
    }
    
    # Step 1: Ask external API which function to call
    system_prompt = (
        "You are an assistant for a TODO list app. "
        "Here are the available functions and their parameters: " + FUNCTIONS_JSON +
        "\nGiven the user query, select the function to call and provide the parameters as JSON."
    )
    api_url = "https://chat-api.malkabruk.co.il/openai"
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ],
        "functions": [
            {
                "name": "get_tasks", 
                "description": "Get all tasks",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "add_task", 
                "description": "Add a new task",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "task": {
                            "type": "object",
                            "description": "Task object to add"
                        }
                    },
                    "required": ["task"]
                }
            },
            {
                "name": "update_task", 
                "description": "Update a task by id",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "task_id": {
                            "type": "string",
                            "description": "ID of the task to update"
                        },
                        "new_task": {
                            "type": "object",
                            "description": "New task data"
                        }
                    },
                    "required": ["task_id", "new_task"]
                }
            },
            {
                "name": "delete_task", 
                "description": "Delete a task by id",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "task_id": {
                            "type": "string",
                            "description": "ID of the task to delete"
                        }
                    },
                    "required": ["task_id"]
                }
            }
        ],
        "function_call": "auto"
    }
    
    print(f"[DEBUG] API URL: {api_url}")
    print(f"[DEBUG] Headers: {headers}")
    print(f"[DEBUG] Payload keys: {list(payload.keys())}")
    print(f"[DEBUG] Model: {payload['model']}")
    print(f"[DEBUG] Messages count: {len(payload['messages'])}")
    print(f"[DEBUG] Functions count: {len(payload['functions'])}")
    
    try:
        print("[DEBUG] Creating httpx client...")
        async with httpx.AsyncClient(verify=False, timeout=30) as client:
            print("[DEBUG] Sending POST request...")
            response = await client.post(api_url, headers=headers, json=payload)
            print(f"[DEBUG] Request completed!")
        
        print(f"[DEBUG] Response status: {response.status_code}")
        print(f"[DEBUG] Response headers: {dict(response.headers)}")
        print(f"[DEBUG] Response content (first 500 chars): {response.text[:500]}")
        
        if len(response.text) > 500:
            print(f"[DEBUG] Response content (full): {response.text}")
            
    except httpx.TimeoutException as e:
        print(f"[DEBUG] Timeout exception: {e}")
        return f"שגיאת timeout בקריאה לשרת: {e}"
    except httpx.RequestError as e:
        print(f"[DEBUG] Request error: {e}")
        return f"שגיאת רשת בקריאה לשרת: {e}"
    except Exception as e:
        print(f"[DEBUG] Unexpected exception in first API call: {e}")
        print(f"[DEBUG] Exception type: {type(e)}")
        import traceback
        traceback.print_exc()
        return f"שגיאה לא צפויה בקריאה לשרת: {e}"
    
    if not response.is_success:
        print(f"[DEBUG] API call failed with status: {response.status_code}")
        print(f"[DEBUG] Error response body: {response.text}")
        return f"תקלה בפנייה לשרת ה-AI. סטטוס: {response.status_code}"
    
    try:
        print("[DEBUG] Attempting to parse JSON response...")
        completion = response.json()
        print(f"[DEBUG] JSON parsed successfully!")
        print(f"[DEBUG] Response structure: {list(completion.keys()) if isinstance(completion, dict) else type(completion)}")
        
        if isinstance(completion, dict) and 'choices' in completion:
            print(f"[DEBUG] Choices count: {len(completion['choices'])}")
            if completion['choices']:
                first_choice = completion['choices'][0]
                print(f"[DEBUG] First choice keys: {list(first_choice.keys()) if isinstance(first_choice, dict) else type(first_choice)}")
                if isinstance(first_choice, dict) and 'message' in first_choice:
                    message = first_choice['message']
                    print(f"[DEBUG] Message keys: {list(message.keys()) if isinstance(message, dict) else type(message)}")
        
    except Exception as e:
        print(f"[DEBUG] Failed to parse JSON: {e}")
        print(f"[DEBUG] Raw response: {response.text}")
        return f"שגיאה בפענוח התשובה: {e}"
    
    function_call = completion.get("choices", [{}])[0].get("message", {}).get("function_call")
    print(f"[DEBUG] Function call extracted: {function_call}")
    
    if not function_call:
        print("[DEBUG] No function call found in response")
        return "לא הצלחתי להבין את הבקשה."
    
    func_name = function_call.get("name")
    print(f"[DEBUG] Function name: {func_name}")
    
    try:
        arguments = json.loads(function_call.get("arguments", "{}"))
        print(f"[DEBUG] Function arguments: {arguments}")
    except Exception as e:
        print(f"[DEBUG] Failed to parse arguments: {e}")
        return f"שגיאה בפענוח הפרמטרים: {e}"

    # Step 2: Call the selected function
    print(f"[DEBUG] Calling function: {func_name}")
    try:
        if func_name == "get_tasks":
            result = get_tasks()
        elif func_name == "add_task":
            result = add_task(arguments["task"])
        elif func_name == "update_task":
            result = update_task(arguments["task_id"], arguments["new_task"])
        elif func_name == "delete_task":
            result = delete_task(arguments["task_id"])
        else:
            print(f"[DEBUG] Unknown function: {func_name}")
            return "הפונקציה ש-GPT ביקש לא קיימת."
        
        print(f"[DEBUG] Function result: {result}")
    except Exception as e:
        print(f"[DEBUG] Exception in function call: {e}")
        return f"שגיאה בביצוע הפעולה: {e}"

    # Step 3: Ask external API to formulate a user-friendly response
    print("[DEBUG] Preparing second API call for response formatting")
    response_prompt = (
        f"User query: {query}\nSystem function: {func_name}\nResult: {result}\n"
        "Please write a human-readable response in Hebrew."
    )
    payload2 = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": "אתה עוזר אישי שמנסח תשובות יפות בעברית."},
            {"role": "user", "content": response_prompt}
        ]
    }
    
    try:
        async with httpx.AsyncClient(verify=False, timeout=30) as client:
            response2 = await client.post(api_url, headers=headers, json=payload2)
        print(f"[DEBUG] Second API response status: {response2.status_code}")
    except Exception as e:
        print(f"[DEBUG] Exception in second API call: {e}")
        return f"שגיאה בקריאה השנייה לשרת: {e}"
    
    if not response2.is_success:
        print(f"[DEBUG] Second API call failed with status: {response2.status_code}")
        return "תקלה בניסוח התשובה."
    
    try:
        completion2 = response2.json()
        final_response = completion2.get("choices", [{}])[0].get("message", {}).get("content", "שגיאה").strip()
        print(f"[DEBUG] Final response: {final_response}")
        return final_response
    except Exception as e:
        print(f"[DEBUG] Exception in parsing final response: {e}")
        return f"שגיאה בפענוח התשובה הסופית: {e}"
