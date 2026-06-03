conversation_memory = []

def add_message(role, content):

    conversation_memory.append(
        {
            "role": role,
            "content": content
        }
    )

def get_history():

    return "\n".join(
        [
            f"{msg['role']}: {msg['content']}"
            for msg in conversation_memory[-10:]
        ]
    )