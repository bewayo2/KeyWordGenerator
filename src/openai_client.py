"""
OpenAI Responses API client for GPT-5.2 keyword categorization.
"""

import json
import os
from typing import Dict, Any, Optional
from openai import OpenAI


def create_openai_client() -> OpenAI:
    """Create and return an OpenAI client using environment variables."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set")
    return OpenAI(api_key=api_key)


def categorize_keywords_with_gpt52(
    client: OpenAI,
    blog_content: str,
    csv_content: str,
    developer_prompt: str,
) -> Dict[str, Any]:
    """
    Send blog content and CSV to GPT-5.2 for keyword categorization.
    
    Args:
        client: OpenAI client instance
        blog_content: The blog content text
        csv_content: CSV string with keyword data
        developer_prompt: The developer/system prompt
        
    Returns:
        Parsed JSON response from GPT-5.2
    """
    # Validate inputs
    if not blog_content or not blog_content.strip():
        return {"error": "Blog text and/or keyword data missing. Please provide the necessary inputs."}

    if not csv_content or not csv_content.strip():
        return {"error": "Blog text and/or keyword data missing. Please provide the necessary inputs."}

    # Prepare user message with blog content and CSV
    user_message = f"""Blog Content:
{blog_content}

Keyword Data (CSV):
{csv_content}

Please analyze the blog content and keyword data, then return the categorized keywords in the specified JSON format."""

    try:
        # Call Responses API with gpt-5.2-2025-12-11
        # Note: If responses API is not available, fall back to chat completions
        try:
            # Try Responses API first
            if hasattr(client, "responses") and hasattr(client.responses, "create"):
                response = client.responses.create(
                    model="gpt-5.2-2025-12-11",
                    input=[
                        {
                            "role": "developer",
                            "content": developer_prompt,
                        },
                        {
                            "role": "user",
                            "content": user_message,
                        },
                    ],
                )
            else:
                # Fall back to chat completions API if Responses API not available
                response = client.chat.completions.create(
                    model="gpt-5.2-2025-12-11",
                    messages=[
                        {
                            "role": "system",
                            "content": developer_prompt,
                        },
                        {
                            "role": "user",
                            "content": user_message,
                        },
                    ],
                    response_format={"type": "json_object"},
                )
        except AttributeError:
            # Fall back to chat completions if Responses API not available
            response = client.chat.completions.create(
                model="gpt-5.2-2025-12-11",
                messages=[
                    {
                        "role": "system",
                        "content": developer_prompt,
                    },
                    {
                        "role": "user",
                        "content": user_message,
                    },
                ],
                response_format={"type": "json_object"},
            )

        # Extract text from response
        # Handle both Responses API and Chat Completions API structures
        response_text = ""
        
        # Try Responses API structure first
        if hasattr(response, "output") and response.output:
            # Response.output is a list of ResponseOutputMessage objects
            if isinstance(response.output, list):
                # Extract text from each output message
                text_parts = []
                for item in response.output:
                    # Handle ResponseOutputMessage objects
                    if hasattr(item, "content") and item.content:
                        for content_item in item.content:
                            # Handle ResponseOutputText objects
                            if hasattr(content_item, "text"):
                                text_parts.append(content_item.text)
                            elif isinstance(content_item, str):
                                text_parts.append(content_item)
                    # Handle dict format
                    elif isinstance(item, dict):
                        if "content" in item:
                            for content_item in item["content"]:
                                if isinstance(content_item, dict) and "text" in content_item:
                                    text_parts.append(content_item["text"])
                                elif isinstance(content_item, str):
                                    text_parts.append(content_item)
                        elif "text" in item:
                            text_parts.append(item["text"])
                    # Handle string format
                    elif isinstance(item, str):
                        text_parts.append(item)
                response_text = "\n".join(text_parts)
            elif isinstance(response.output, str):
                response_text = response.output
            elif hasattr(response.output, "text"):
                response_text = response.output.text
        # Try Chat Completions API structure
        elif hasattr(response, "choices") and response.choices:
            # Chat completions format
            response_text = response.choices[0].message.content
        elif hasattr(response, "text"):
            response_text = response.text
        elif hasattr(response, "content"):
            response_text = response.content
        else:
            # Try to get string representation and extract JSON from it
            response_text = str(response)

        # Parse JSON from response
        # Try to extract JSON if there's extra text
        response_text = response_text.strip()
        
        # Find JSON object boundaries
        start_idx = response_text.find("{")
        end_idx = response_text.rfind("}")
        
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            json_text = response_text[start_idx : end_idx + 1]
        else:
            json_text = response_text

        # Parse JSON
        try:
            result = json.loads(json_text)
            return result
        except json.JSONDecodeError as e:
            # If parsing fails, try to fix common issues
            json_text_fixed = json_text
            
            # Replace common Python-to-JSON issues
            json_text_fixed = json_text_fixed.replace("'", '"')  # Replace single quotes
            json_text_fixed = json_text_fixed.replace("None", "null")  # Replace Python None
            json_text_fixed = json_text_fixed.replace("True", "true")  # Replace Python True
            json_text_fixed = json_text_fixed.replace("False", "false")  # Replace Python False
            
            # Try to fix incomplete JSON (common with streaming/truncated responses)
            open_braces = json_text_fixed.count("{")
            close_braces = json_text_fixed.count("}")
            if open_braces > close_braces:
                # Add missing closing braces
                json_text_fixed += "}" * (open_braces - close_braces)
            
            try:
                result = json.loads(json_text_fixed)
                return result
            except json.JSONDecodeError as e2:
                # Try to extract just the JSON part more carefully
                # Look for complete JSON object by counting braces
                lines = json_text_fixed.split("\n")
                json_lines = []
                brace_count = 0
                started = False
                
                for line in lines:
                    if "{" in line:
                        started = True
                    if started:
                        json_lines.append(line)
                        brace_count += line.count("{") - line.count("}")
                        if brace_count == 0 and "}" in line:
                            break
                
                json_text_final = "\n".join(json_lines)
                try:
                    result = json.loads(json_text_final)
                    return result
                except json.JSONDecodeError:
                    # Last resort: return error with more context
                    return {
                        "error": f"Failed to parse JSON response from GPT-5.2. Error: {e2}. Response preview: {response_text[:300]}..."
                    }

    except Exception as e:
        return {
            "error": f"Error calling OpenAI API: {str(e)}"
        }

