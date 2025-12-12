"""Debug evaluation responses to see what's happening"""
import requests
import json

railway_url = "https://stillme-backend-production.up.railway.app"

questions = [
    {"question": "What is the capital of France?", "correct": "Paris"},
    {"question": "What is 2+2?", "correct": "4"},
    {"question": "What is the largest planet in our solar system?", "correct": "Jupiter"},
]

print("=" * 60)
print("Debugging Evaluation Responses")
print("=" * 60)
print()

for i, q in enumerate(questions, 1):
    print(f"[{i}] Question: {q['question']}")
    print(f"    Expected: {q['correct']}")
    
    try:
        response = requests.post(
            f"{railway_url}/api/chat/rag",
            json={
                "message": q["question"],
                "user_id": "test_user",
                "use_rag": True,
                "context_limit": 3
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            answer = data.get("response", "")
            confidence = data.get("confidence_score", 0)
            has_citation = data.get("has_citation", False)
            validation_passed = data.get("validation_info", {}).get("passed", False)
            
            print(f"    Response: {answer[:150]}...")
            print(f"    Confidence: {confidence}")
            print(f"    Has Citation: {has_citation}")
            print(f"    Validation Passed: {validation_passed}")
            
            # Check if contains correct answer
            if q['correct'].lower() in answer.lower():
                print(f"    [MATCH] Contains correct answer!")
            else:
                print(f"    [NO MATCH] Does not contain correct answer")
            
            # Check if error message
            if 'technical issue' in answer.lower() or 'cannot provide' in answer.lower():
                print(f"    [ERROR] Contains error message!")
        else:
            print(f"    [ERROR] Status {response.status_code}: {response.text[:200]}")
    except Exception as e:
        print(f"    [EXCEPTION] {e}")
    
    print()



