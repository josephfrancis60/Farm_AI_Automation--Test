import os
# from langchain_groq import ChatGroq
# from langchain_openai import ChatOpenAI
import asyncio
import base64
from fastapi import WebSocket, WebSocketDisconnect
from google import genai
from google.genai import types
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

# Import tools for live session for Gemini Live Audio API
from tools.agent_tools import (
    crops, set_reminder, check_irrigation_status, add_new_crop, 
    update_existing_field, delete_crop_field, fertilizer, inventory,
    add_inventory_item, update_inventory_stock, remove_from_inventory,
    irrigation, update_weather_history, weather, manage_database_table,
    clear_alerts, clear_reminders, get_irrigation_schedule_for_crop,
    add_irrigation_schedule, remove_irrigation_schedule, get_irrigation_history
)

load_dotenv()

# MODEL_NAME = "openai/gpt-oss-120b:free"  # Openrouter
# MODEL_NAME = "llama-3.3-70b-versatile"  # GroqCloud
MODEL_NAME = os.getenv("GEMINI_LIVE_MODEL", "gemini-2.5-flash-native-audio-preview-12-2025")
TEXT_MODEL_NAME = os.getenv("GEMINI_TEXT_MODEL", "gemini-2.5-flash")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


def normalize_live_text(value):
    """
    Gemini SDK transcript fields can be strings or structured content parts.
    Keep the Web UI contract simple: always send a displayable string.
    """
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        text = value.get("text")
        if text is not None:
            return normalize_live_text(text)
        return str(value)
    text = getattr(value, "text", None)
    if text is not None and text is not value:
        return normalize_live_text(text)
    return str(value)


def modality_counts(details):
    if not details:
        return {}
    counts = {}
    for detail in details:
        modality = normalize_live_text(getattr(detail, "modality", "unknown")).lower()
        counts[modality] = getattr(detail, "token_count", 0) or 0
    return counts


def get_llm():

    # llm = ChatGroq(
    #     model=MODEL_NAME,
    #     api_key=os.getenv("GROQ_API_KEY"),
    #     temperature=0.4 # 0.0 means no creativity and 1.0 means more creativity
    # )

    # llm = ChatOpenAI(
    #     model=MODEL_NAME,
    #     openai_api_key=os.getenv("OPENROUTER_API_KEY"),
    #     openai_api_base="https://openrouter.ai/api/v1",
    #     temperature=0.4
    # )

    # return llm

    """
    Returns a standard LangChain LLM object for text-based interactions.
    """
    return ChatGoogleGenerativeAI(
        model=TEXT_MODEL_NAME,
        google_api_key=GEMINI_API_KEY,
        temperature=0.4
    )

def get_gemini_tools():
    """
    Returns tool definitions for Gemini Live API.
    """
    return [
        types.Tool(
            function_declarations=[
                types.FunctionDeclaration(
                    name="crops",
                    description="Get the list of all crops currently growing in the farm.",
                    parameters=types.Schema(type="OBJECT", properties={})
                ),
                types.FunctionDeclaration(
                    name="set_reminder",
                    description="Set a reminder for the user.",
                    parameters=types.Schema(
                        type="OBJECT",
                        properties={
                            "title": types.Schema(type="STRING"),
                            "message": types.Schema(type="STRING"),
                            "delay_minutes": types.Schema(type="NUMBER")
                        },
                        required=["title", "message"]
                    )
                ),
                types.FunctionDeclaration(
                    name="check_irrigation_status",
                    description="Check the irrigation schedule and compare with weather.",
                    parameters=types.Schema(
                        type="OBJECT",
                        properties={"city": types.Schema(type="STRING")},
                        required=["city"]
                    )
                ),
                types.FunctionDeclaration(
                    name="weather",
                    description="Get the current weather and forecast for a specific city.",
                    parameters=types.Schema(
                        type="OBJECT",
                        properties={"city": types.Schema(type="STRING")},
                        required=["city"]
                    )
                ),
                types.FunctionDeclaration(
                    name="inventory",
                    description="Check the current stock of fertilizers in the inventory.",
                    parameters=types.Schema(type="OBJECT", properties={})
                ),
                types.FunctionDeclaration(
                    name="irrigation",
                    description="Activate or schedule the sprinkler irrigation system.",
                    parameters=types.Schema(
                        type="OBJECT",
                        properties={
                            "field_id": types.Schema(type="INTEGER"),
                            "duration_minutes": types.Schema(type="INTEGER"),
                            "delay_minutes": types.Schema(type="NUMBER")
                        },
                        required=["field_id", "duration_minutes"]
                    )
                ),
                types.FunctionDeclaration(
                    name="get_irrigation_history",
                    description="Retrieve recent irrigation history.",
                    parameters=types.Schema(
                        type="OBJECT",
                        properties={
                            "crop_name": types.Schema(type="STRING"),
                            "limit": types.Schema(type="INTEGER")
                        }
                    )
                )
            ]
        )
    ]

async def handle_live_chat(websocket: WebSocket):
    """
    Handles the WebSocket connection for Gemini Live bidirectional voice.
    """
    await websocket.accept()

    if not GEMINI_API_KEY:
        await websocket.send_json({
            "type": "error",
            "message": "GEMINI_API_KEY is not set in backend/.env."
        })
        await websocket.close()
        return
    
    # Initialize Gemini client
    client = genai.Client(api_key=GEMINI_API_KEY, http_options={'api_version': 'v1alpha'})
    
    try:
        # Initial config wait
        config_data = await websocket.receive_json()
        model_id = config_data.get("model", MODEL_NAME)
        voice_name = config_data.get("voice", "Kore")
        language = config_data.get("language", "English")
        
        enable_affective = config_data.get("affective_dialog", True)
        enable_proactive = config_data.get("proactive_audio", True)
        
        session_config = types.LiveConnectConfig(
            response_modalities=[types.Modality.AUDIO],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=voice_name
                    )
                )
            ),
            tools=get_gemini_tools(),
            system_instruction=types.Content(
                parts=[types.Part(text=(
                    f"You are ECHO, a professional farm assistant. Always respond in {language}. "
                    f"If the user speaks in another language, understand their intent and still reply in {language}. "
                    f"Do not reply in English unless the configured language is English. "
                    f"Be concise and helpful. You have access to tools for managing crops, irrigation, reminders, and inventory."
                ))]
            ),
            enable_affective_dialog=enable_affective,
            proactivity=types.ProactivityConfig(proactive_audio=enable_proactive),
            output_audio_transcription=types.AudioTranscriptionConfig(),
            input_audio_transcription=types.AudioTranscriptionConfig()
        )
        
        async with client.aio.live.connect(model=model_id, config=session_config) as session:
            
            async def send_to_client():
                async for message in session.receive():
                    # Audio data
                    if message.data:
                        await websocket.send_json({
                            "type": "audio",
                            "data": base64.b64encode(message.data).decode('utf-8')
                        })
                    elif message.server_content and message.server_content.model_turn:
                        for part in message.server_content.model_turn.parts:
                            if part.inline_data:
                                await websocket.send_json({
                                    "type": "audio",
                                    "data": base64.b64encode(part.inline_data.data).decode('utf-8')
                                })
                    
                    # Transcripts
                    if message.server_content and message.server_content.output_transcription:
                        text = normalize_live_text(message.server_content.output_transcription.text)
                        print(f"Gemini: {text}")
                        await websocket.send_json({
                            "type": "transcript",
                            "role": "echo",
                            "text": text,
                            "finished": bool(message.server_content.output_transcription.finished)
                        })
                    
                    if message.server_content and message.server_content.input_transcription:
                        text = normalize_live_text(message.server_content.input_transcription.text)
                        print(f"User: {text}")
                        await websocket.send_json({
                            "type": "transcript",
                            "role": "user",
                            "text": text,
                            "finished": bool(message.server_content.input_transcription.finished)
                        })

                    # Tool calls
                    if message.tool_call:
                        tool_responses = []
                        for call in message.tool_call.function_calls:
                            name = call.name
                            args = call.args
                            
                            try:
                                if name == "crops": result = crops.run({})
                                elif name == "set_reminder": result = set_reminder.run(args)
                                elif name == "check_irrigation_status": result = check_irrigation_status.run(args)
                                elif name == "weather": result = weather.run(args)
                                elif name == "inventory": result = inventory.run({})
                                elif name == "irrigation": result = irrigation.run(args)
                                elif name == "get_irrigation_history": result = get_irrigation_history.run(args)
                                else: result = f"Tool {name} not found."
                                
                                tool_responses.append(types.FunctionResponse(
                                    id=call.id,
                                    name=name,
                                    response={"result": str(result)}
                                ))
                            except Exception as e:
                                tool_responses.append(types.FunctionResponse(
                                    id=call.id,
                                    name=name,
                                    response={"error": str(e)}
                                ))
                        
                        await session.send_tool_response(function_responses=tool_responses)

                    # Usage metadata
                    if message.usage_metadata:
                        usage = message.usage_metadata
                        await websocket.send_json({
                            "type": "usage",
                            "total_tokens": usage.total_token_count or 0,
                            "prompt_tokens": usage.prompt_token_count or 0,
                            "response_tokens": usage.response_token_count or 0,
                            "thoughts_tokens": usage.thoughts_token_count or 0,
                            "prompt_tokens_details": modality_counts(usage.prompt_tokens_details),
                            "response_tokens_details": modality_counts(usage.response_tokens_details)
                        })

            async def receive_from_client():
                while True:
                    try:
                        data = await websocket.receive_json()
                        if data["type"] == "audio":
                            audio_bytes = base64.b64decode(data["data"])
                            await session.send_realtime_input(audio=types.Blob(
                                data=audio_bytes,
                                mime_type="audio/pcm;rate=16000"
                            ))
                        elif data["type"] == "text":
                            await session.send_realtime_input(text=data["text"])
                        elif data["type"] == "end":
                            await session.send_realtime_input(audio_stream_end=True)
                    except WebSocketDisconnect:
                        break
                    except Exception as e:
                        await websocket.send_json({
                            "type": "error",
                            "message": f"Live input error: {e}"
                        })
                        break

            await asyncio.gather(send_to_client(), receive_from_client())

    except Exception as e:
        print(f"WebSocket session error: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e)
            })
        except Exception:
            pass
        await websocket.close()
