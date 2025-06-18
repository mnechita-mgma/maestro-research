import json
import time
from dataclasses import dataclass
from typing import List, Optional

from dotenv import load_dotenv
from flask import Flask, request, Response
from langchain_core.messages import HumanMessage
from opik.integrations.langchain import OpikTracer

from graph import create_graph


load_dotenv()

tracer = OpikTracer(project_name="ai-bus-nano-demo")
orchestrator = create_graph()
app = Flask(__name__)


@dataclass
class SSEMessage:
    data: Optional[List[str]] = None  # Make data optional
    event: Optional[str] = None
    id: Optional[str] = None
    retry: Optional[int] = None
    
    def to_sse_string(self) -> str:
        lines = []
        if self.data:  # Only add data lines if data exists
            for d in self.data:
                lines.append(f"data:{d}")
        if self.event:
            lines.append(f"event:{self.event}")
        if self.id:
            lines.append(f"id:{self.id}")
        if self.retry is not None:
            lines.append(f"retry:{self.retry}")
        return "\n".join(lines) + "\n\n"
    
    
@app.route('/ai-buzz/streamUnderstand', methods=['POST'])
def understand():
    # Parse the JSON from the multipart form data
    metadata = request.form.get('metadata')
    if not metadata:
        return "No metadata provided", 400

    try:
        data = json.loads(metadata)
        print(data)
        
    except json.JSONDecodeError:
        return "Invalid JSON in metadata", 400 
    
    with open("audio.json") as f:
        audio_beep = json.load(f)

    def generate():
        # thinking_d = {"text": "thinking...", "audioBytes": audio_beep}
        # for i in range(3):
        #     time.sleep(1.5)
        #     thinking_msg = SSEMessage(
        #         data=[json.dumps(thinking_d)],
        #         event="audio",
        #         id=str(int(time.time() * 100))
        #     )
        #     yield thinking_msg.to_sse_string()

        # Final message
        responses = orchestrator.invoke(
            input={"messages": [HumanMessage(data["transcription"])]},
            config={"callbacks": [tracer], "configurable": {"thread_id": "thread-1"}}

        )
        final_response = responses["messages"][-1].content
        resp_d = {"text": final_response, "audioBytes": None}
        resp_msg = SSEMessage(
            data=[json.dumps(resp_d)],
            event="audio",
            id=str(int(time.time() * 100))
        )
        yield resp_msg.to_sse_string()
    
    return Response(
        generate(),
        content_type='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Access-Control-Allow-Origin': '*',
            'X-Accel-Buffering': 'no'  # Disable nginx buffering
        }
    )


if __name__ == '__main__':
    app.run("0.0.0.0", 8080, debug=True, threaded=True)