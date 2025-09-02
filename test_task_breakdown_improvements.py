#!/usr/bin/env python3
"""
Test script for task breakdown improvements
"""

from xandai.task_manager import TaskManager

def test_project_type_detection():
    """Test the improved project type detection"""
    tm = TaskManager()
    
    test_cases = [
        {
            'request': 'Create a web-based chat interface that integrates with Ollama API running at 192.168.3.70:11434. The frontend should feature Bootstrap UI with modern JavaScript for real-time chat.',
            'expected_type': 'frontend'
        },
        {
            'request': 'Build a Flask API with database integration and user authentication',
            'expected_type': 'backend'  
        },
        {
            'request': 'Create a fullstack e-commerce application with React frontend and Django backend',
            'expected_type': 'fullstack'
        },
        {
            'request': 'Write a Python script to process CSV data and generate reports',
            'expected_type': 'data_script'
        }
    ]
    
    print("=== Testing Project Type Detection ===")
    for i, test_case in enumerate(test_cases, 1):
        detected = tm._detect_project_type(test_case['request'])
        expected = test_case['expected_type']
        status = "✅" if detected == expected else "❌"
        
        print(f"{i}. {status} Expected: {expected}, Got: {detected}")
        print(f"   Request: {test_case['request'][:60]}...")
        print()

def test_framework_detection():
    """Test the improved contextual framework detection"""
    print("=== Testing Framework Detection ===")
    
    test_cases = [
        {
            'request': 'Create a web-based chat interface with Bootstrap for styling',
            'should_detect': 'Bootstrap',
            'should_not_detect': 'Flask'
        },
        {
            'request': 'Build a Flask API with user authentication endpoints',
            'should_detect': 'Flask',
            'should_not_detect': 'React'
        },
        {
            'request': 'Create a React component for displaying user profiles',
            'should_detect': 'React', 
            'should_not_detect': 'Django'
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        tm = TaskManager()  # Fresh instance for each test
        tm.detect_context(test_case['request'])
        
        detected_framework = tm.global_context.get('framework')
        should_detect = test_case['should_detect']
        should_not_detect = test_case['should_not_detect']
        
        correct_positive = detected_framework == should_detect
        correct_negative = detected_framework != should_not_detect
        
        status = "✅" if correct_positive else "❌"
        print(f"{i}. {status} Request: {test_case['request'][:50]}...")
        print(f"   Expected: {should_detect}, Got: {detected_framework}")
        if not correct_negative:
            print(f"   ⚠️  Should NOT have detected: {should_not_detect}")
        print()

def test_breakdown_prompt():
    """Test the improved breakdown prompt generation"""
    print("=== Testing Breakdown Prompt Generation ===")
    
    tm = TaskManager()
    request = "Create a web-based chat interface with Bootstrap and JavaScript"
    
    prompt = tm.get_breakdown_prompt(request)
    
    # Check for improvements
    improvements_found = []
    if "PROJECT TYPE DETECTION" in prompt:
        improvements_found.append("✅ Project type detection instructions")
    if "AVOID COMMON MISTAKES" in prompt:
        improvements_found.append("✅ Mistake avoidance guidelines")
    if "Frontend/Client-side" in prompt:
        improvements_found.append("✅ Project type examples")
    if "Generate ONLY the numbered task list" in prompt:
        improvements_found.append("✅ Clear output format instructions")
    
    print("Improvements found in breakdown prompt:")
    for improvement in improvements_found:
        print(f"  {improvement}")
    
    print(f"\nPrompt length: {len(prompt)} characters")
    print("✅ Breakdown prompt generated successfully!")

if __name__ == "__main__":
    test_project_type_detection()
    test_framework_detection()
    test_breakdown_prompt()
    print("\n🎉 All task breakdown improvement tests completed!")
