"""
Module for communication with OLLAMA API
"""

import json
import requests
from typing import Dict, List, Optional, Generator
from urllib.parse import urljoin


class OllamaAPIError(Exception):
    """Custom exception for OLLAMA API errors"""
    pass


class OllamaAPI:
    """Cliente para interagir com a API OLLAMA"""
    
    def __init__(self, endpoint: str = "http://localhost:11434"):
        """
        Initializes the OLLAMA API client
        
        Args:
            endpoint: Base URL of OLLAMA API
        """
        self.endpoint = endpoint.rstrip('/')
        self.session = requests.Session()
        
    def _make_request(self, method: str, path: str, **kwargs) -> requests.Response:
        """
        Makes an HTTP request to the API
        
        Args:
            method: HTTP method (GET, POST, etc.)
            path: API path
            **kwargs: Additional arguments for requests
            
        Returns:
            Request response
            
        Raises:
            OllamaAPIError: If there is an error in the request
        """
        url = urljoin(self.endpoint + '/', path.lstrip('/'))
        
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.ConnectionError:
            raise OllamaAPIError(f"Could not connect to OLLAMA API at {self.endpoint}")
        except requests.exceptions.Timeout:
            raise OllamaAPIError("Timeout trying to connect to OLLAMA API")
        except requests.exceptions.HTTPError as e:
            raise OllamaAPIError(f"Erro HTTP: {e}")
        except Exception as e:
            raise OllamaAPIError(f"Erro inesperado: {e}")
    
    def list_models(self) -> List[Dict[str, any]]:
        """
        Lists all available models in OLLAMA API
        
        Returns:
            List of dictionaries with model information
            
        Raises:
            OllamaAPIError: Se houver erro ao listar modelos
        """
        try:
            response = self._make_request('GET', '/api/tags')
            data = response.json()
            return data.get('models', [])
        except json.JSONDecodeError:
            raise OllamaAPIError("Invalid API response when listing models")
    
    def generate(self, model: str, prompt: str, stream: bool = True) -> Generator[str, None, None]:
        """
        Gera uma resposta usando o modelo especificado
        
        Args:
            model: Nome do modelo a usar
            prompt: Prompt para o modelo
            stream: Se deve retornar resposta em streaming
            
        Yields:
            Response parts as they are generated
            
        Raises:
            OllamaAPIError: If there is an error in generation
        """
        payload = {
            'model': model,
            'prompt': prompt,
            'stream': stream
        }
        
        try:
            response = self._make_request(
                'POST',
                '/api/generate',
                json=payload,
                stream=stream
            )
            
            if stream:
                for line in response.iter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            if 'response' in data:
                                yield data['response']
                            if data.get('done', False):
                                break
                        except json.JSONDecodeError:
                            continue
            else:
                data = response.json()
                yield data.get('response', '')
                
        except json.JSONDecodeError:
            raise OllamaAPIError("Invalid API response when generating text")
    
    def test_connection(self) -> bool:
        """
        Tests connection with OLLAMA API
        
        Returns:
            True if connection was successful, False otherwise
        """
        try:
            self._make_request('GET', '/')
            return True
        except OllamaAPIError:
            return False
