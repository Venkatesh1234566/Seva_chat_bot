import re
 
def extract_session_id(session_str:str):
    match=re.search(r"/session/(.*?)/contexts/", session_str)
    if match:
        extracted_string=match.group(1)
        return extracted_string
    
    return ""


def get_str_from_book_dict(book_dict:dict):
    return ", ".join([f"{int(value)} {key}" for key, value in book_dict.items()])


if __name__=="__main__":
    extract_session_id("projects/final-chat-expd/agent/sessions/b289533a-f2d6-3452-76b3-c68f052068fa/contexts/ongoing-order")