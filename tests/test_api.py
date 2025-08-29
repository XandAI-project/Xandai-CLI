"""
Testes para o módulo api
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock

from xandai.api import OllamaAPI, OllamaAPIError


class TestOllamaAPI:
    """Testes para a classe OllamaAPI"""
    
    @pytest.fixture
    def api(self):
        """Cria uma instância da API para testes"""
        return OllamaAPI("http://localhost:11434")
    
    def test_init(self):
        """Testa inicialização da API"""
        api = OllamaAPI("http://example.com:8080")
        assert api.endpoint == "http://example.com:8080"
    
    def test_init_strips_trailing_slash(self):
        """Testa que barras finais são removidas do endpoint"""
        api = OllamaAPI("http://example.com/")
        assert api.endpoint == "http://example.com"
    
    @patch('xandai.api.requests.Session')
    def test_make_request_success(self, mock_session, api):
        """Testa requisição bem-sucedida"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "ok"}
        
        mock_session.return_value.request.return_value = mock_response
        api.session = mock_session.return_value
        
        response = api._make_request('GET', '/test')
        
        assert response == mock_response
        mock_session.return_value.request.assert_called_once()
    
    @patch('xandai.api.requests.Session')
    def test_make_request_connection_error(self, mock_session, api):
        """Testa erro de conexão"""
        import requests
        mock_session.return_value.request.side_effect = requests.exceptions.ConnectionError()
        api.session = mock_session.return_value
        
        with pytest.raises(OllamaAPIError) as exc_info:
            api._make_request('GET', '/test')
        
        assert "Não foi possível conectar" in str(exc_info.value)
    
    @patch('xandai.api.requests.Session')
    def test_list_models_success(self, mock_session, api):
        """Testa listagem de modelos bem-sucedida"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "models": [
                {"name": "llama2:latest", "size": 1000000},
                {"name": "codellama:latest", "size": 2000000}
            ]
        }
        
        mock_session.return_value.request.return_value = mock_response
        api.session = mock_session.return_value
        
        models = api.list_models()
        
        assert len(models) == 2
        assert models[0]["name"] == "llama2:latest"
    
    @patch('xandai.api.requests.Session')
    def test_list_models_empty(self, mock_session, api):
        """Testa listagem quando não há modelos"""
        mock_response = Mock()
        mock_response.json.return_value = {"models": []}
        
        mock_session.return_value.request.return_value = mock_response
        api.session = mock_session.return_value
        
        models = api.list_models()
        
        assert models == []
    
    @patch('xandai.api.requests.Session')
    def test_generate_streaming(self, mock_session, api):
        """Testa geração de texto com streaming"""
        # Simula resposta em streaming
        mock_response = Mock()
        mock_response.iter_lines.return_value = [
            b'{"response": "Hello", "done": false}',
            b'{"response": " World", "done": false}',
            b'{"response": "!", "done": true}'
        ]
        
        mock_session.return_value.request.return_value = mock_response
        api.session = mock_session.return_value
        
        result = list(api.generate("llama2", "Say hello", stream=True))
        
        assert result == ["Hello", " World", "!"]
        
        # Verifica que a requisição foi feita corretamente
        call_args = mock_session.return_value.request.call_args
        assert call_args[0] == ('POST', 'http://localhost:11434/api/generate')
        assert call_args[1]['json']['model'] == 'llama2'
        assert call_args[1]['json']['prompt'] == 'Say hello'
        assert call_args[1]['json']['stream'] == True
    
    @patch('xandai.api.requests.Session')
    def test_generate_non_streaming(self, mock_session, api):
        """Testa geração de texto sem streaming"""
        mock_response = Mock()
        mock_response.json.return_value = {"response": "Hello World!"}
        
        mock_session.return_value.request.return_value = mock_response
        api.session = mock_session.return_value
        
        result = list(api.generate("llama2", "Say hello", stream=False))
        
        assert result == ["Hello World!"]
    
    @patch('xandai.api.requests.Session')
    def test_test_connection_success(self, mock_session, api):
        """Testa verificação de conexão bem-sucedida"""
        mock_response = Mock()
        mock_response.status_code = 200
        
        mock_session.return_value.request.return_value = mock_response
        api.session = mock_session.return_value
        
        assert api.test_connection() == True
    
    @patch('xandai.api.requests.Session')
    def test_test_connection_failure(self, mock_session, api):
        """Testa verificação de conexão com falha"""
        import requests
        mock_session.return_value.request.side_effect = requests.exceptions.ConnectionError()
        api.session = mock_session.return_value
        
        assert api.test_connection() == False
