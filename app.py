from flask import Flask, render_template, request, jsonify, Response
import requests
import time
import socket
import json

app = Flask(__name__)

# Ollama API configuration
OLLAMA_HOST = "http://localhost:11434"
MODELS_CACHE = []
LAST_REFRESH = 0

def get_ollama_models():
    """Fetch available models from Ollama with caching"""
    global MODELS_CACHE, LAST_REFRESH
    
    # Refresh every 5 minutes
    if time.time() - LAST_REFRESH > 300 or not MODELS_CACHE:
        try:
            response = requests.get(f"{OLLAMA_HOST}/api/tags")
            if response.status_code == 200:
                MODELS_CACHE = [model['name'] for model in response.json().get('models', [])]
                LAST_REFRESH = time.time()
        except requests.exceptions.RequestException:
            MODELS_CACHE = []
    
    return MODELS_CACHE

def generate_response(model, prompt, context=None):
    """Generate a response from the specified model, stopping at double newline"""
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "context": context or [],
        "options": {"stop": ["\n\n"]}
    }
    
    try:
        response = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json=payload,
            timeout=120
        )
        if response.status_code == 200:
            result = response.json()
            # Stop at first occurrence of double newline
            if '\n\n' in result['response']:
                result['response'] = result['response'].split('\n\n', 1)[0]
            return result
    except requests.exceptions.RequestException:
        pass
    return None

def generate_response_stream(model, prompt, context=None):
    """Generate a streaming response with stop at double newline"""
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": True,
        "context": context or [],
        "options": {"stop": ["\n\n"]}
    }
    
    try:
        response = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json=payload,
            stream=True,
            timeout=120
        )
        context_val = None
        for line in response.iter_lines():
            if line:
                try:
                    chunk = json.loads(line.decode('utf-8'))
                    if not chunk.get("done", False):
                        yield chunk.get("response", "")
                    else:
                        context_val = chunk.get("context")
                except json.JSONDecodeError:
                    continue
        # Return context at the end
        return context_val
    except requests.exceptions.RequestException:
        return None

def get_prompt(style, topic, previous_message, turn_index):
    """Generate appropriate prompt based on discussion style"""
    if turn_index == 0:
        if style == "debate":
            return f"Debate the topic: '{topic}'. Take a strong position and present your argument in a single concise paragraph. End with two newlines."
        elif style == "agree":
            return f"Find common ground on the topic: '{topic}'. Start the conversation with a positive and agreeable statement in a single concise paragraph. End with two newlines."
        elif style == "theorize":
            return f"Theorize about the topic: '{topic}'. Present an initial idea or theory in a single concise paragraph. End with two newlines."
        else:  # discuss
            return f"Discuss the topic: '{topic}'. Start the conversation with a single concise paragraph. End with two newlines."
    else:
        if style == "debate":
            return f"Counter the previous argument: '{previous_message}'. Present your opposing view concisely. End with two newlines."
        elif style == "agree":
            return f"The previous speaker said: '{previous_message}'. Reply positively and build consensus. End with two newlines."
        elif style == "theorize":
            return f"Building on the previous idea: '{previous_message}'. Expand the theory concisely. End with two newlines."
        else:  # discuss
            return f"Continue discussing '{topic}'. Previous message: '{previous_message}'. Reply concisely. End with two newlines."

@app.route('/')
def index():
    """Main page with model selection"""
    models = get_ollama_models()
    return render_template('index.html', models=models)

@app.route('/discuss', methods=['POST'])
def discuss():
    """Initiate discussion between two AI models"""
    data = request.json
    model1 = data.get('model1')
    model2 = data.get('model2')
    topic = data.get('topic')
    turns = int(data.get('turns', 2))
    style = data.get('style', 'discuss')
    
    if not model1 or not model2 or not topic:
        return jsonify({"error": "Missing required parameters"}), 400
    
    conversation = []
    context1 = None
    context2 = None
    
    # First model initiates the conversation
    first_prompt = get_prompt(style, topic, None, 0)
    result1 = generate_response(model1, first_prompt)
    
    if not result1:
        return jsonify({"error": f"{model1} failed to respond"}), 500
    
    conversation.append({
        "model": model1,
        "text": result1['response'],
        "turn": 0
    })
    context1 = result1.get('context')
    
    # Subsequent turns
    for turn in range(1, turns * 2):
        try:
            if turn % 2 == 1:  # Model2's turn
                prompt = get_prompt(style, topic, conversation[-1]['text'], turn)
                result = generate_response(model2, prompt, context2)
                model_name = model2
                context_var = context2
            else:  # Model1's turn
                prompt = get_prompt(style, topic, conversation[-1]['text'], turn)
                result = generate_response(model1, prompt, context1)
                model_name = model1
                context_var = context1
                
            if not result:
                break
                
            conversation.append({
                "model": model_name,
                "text": result['response'],
                "turn": turn
            })
            
            # Update context for next turn
            if turn % 2 == 1:
                context2 = result.get('context')
            else:
                context1 = result.get('context')
                
        except Exception as e:
            conversation.append({
                "error": f"Error on turn {turn}: {str(e)}"
            })
            break
    
    return jsonify({"conversation": conversation})

@app.route('/discuss-stream')
def discuss_stream():
    """Stream discussion between two AI models in real-time"""
    model1 = request.args.get('model1')
    model2 = request.args.get('model2')
    topic = request.args.get('topic')
    turns = request.args.get('turns', default=2, type=int)
    style = request.args.get('style', default='discuss', type=str)
    
    if not model1 or not model2 or not topic:
        def error_generator():
            yield f"data: {json.dumps({'type': 'error', 'content': 'Missing required parameters'})}\n\n"
        return Response(error_generator(), mimetype='text/event-stream')
    
    def generate():
        try:
            # Initial system message
            style_names = {
                "discuss": "discussion",
                "debate": "debate",
                "agree": "consensus-building",
                "theorize": "theory-building"
            }
            style_name = style_names.get(style, "discussion")
            yield f"data: {json.dumps({'type': 'system', 'content': f'Starting {style_name} about: {topic}'})}\n\n"
            
            context1 = None
            context2 = None
            full_response = ""
            
            # First model initiates conversation
            prompt1 = get_prompt(style, topic, None, 0)
            yield f"data: {json.dumps({'type': 'turn_start', 'model': model1, 'turn': 0})}\n\n"
            
            gen = generate_response_stream(model1, prompt1, context1)
            try:
                while True:
                    chunk = next(gen)
                    full_response += chunk
                    yield f"data: {json.dumps({'type': 'chunk', 'model': model1, 'content': chunk})}\n\n"
            except StopIteration as e:
                context1 = e.value  # Capture context from generator
            
            yield f"data: {json.dumps({'type': 'turn_end', 'model': model1, 'content': full_response})}\n\n"
            
            # Subsequent turns
            for turn in range(1, turns * 2):
                current_model = model2 if turn % 2 == 1 else model1
                context = context2 if turn % 2 == 1 else context1
                
                prompt = get_prompt(style, topic, full_response, turn)
                
                yield f"data: {json.dumps({'type': 'turn_start', 'model': current_model, 'turn': turn})}\n\n"
                
                full_response = ""
                gen = generate_response_stream(current_model, prompt, context)
                try:
                    while True:
                        chunk = next(gen)
                        full_response += chunk
                        yield f"data: {json.dumps({'type': 'chunk', 'model': current_model, 'content': chunk})}\n\n"
                except StopIteration as e:
                    context_val = e.value
                
                # Update context for next turn
                if turn % 2 == 1:
                    context2 = context_val
                else:
                    context1 = context_val
                    
                yield f"data: {json.dumps({'type': 'turn_end', 'model': current_model, 'content': full_response})}\n\n"
                
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': f'Error: {str(e)}'})}\n\n"
    
    return Response(generate(), mimetype='text/event-stream')

def get_local_ip():
    """Get local IP address for network access"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "localhost"

if __name__ == '__main__':
    port = 9000
    local_ip = get_local_ip()
    print("\n" + "="*60)
    print(f"🔥 AI Discussion Panel is running!")
    print(f"🌐 Access the application at:")
    print(f"   Local: http://localhost:{port}")
    if local_ip != "localhost":
        print(f"   Network: http://{local_ip}:{port}")
    print("="*60 + "\n")
    
    app.run(host='0.0.0.0', port=port, debug=True)