"""
Testes para o módulo file_operations
"""

import pytest
from pathlib import Path
import tempfile
import shutil

from xandai.file_operations import FileOperations, FileOperationError


@pytest.fixture
def temp_dir():
    """Cria um diretório temporário para testes"""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def file_ops():
    """Cria uma instância de FileOperations"""
    return FileOperations(confirm_before_delete=False)


class TestFileOperations:
    """Testes para a classe FileOperations"""
    
    def test_create_file(self, file_ops, temp_dir):
        """Testa criação de arquivo"""
        test_file = temp_dir / "test.txt"
        content = "Hello, World!"
        
        file_ops.create_file(test_file, content)
        
        assert test_file.exists()
        assert test_file.read_text() == content
    
    def test_create_file_with_subdirs(self, file_ops, temp_dir):
        """Testa criação de arquivo em subdiretórios"""
        test_file = temp_dir / "sub" / "dir" / "test.txt"
        content = "Nested file"
        
        file_ops.create_file(test_file, content)
        
        assert test_file.exists()
        assert test_file.read_text() == content
    
    def test_edit_file(self, file_ops, temp_dir):
        """Testa edição de arquivo"""
        test_file = temp_dir / "test.txt"
        original_content = "Original"
        new_content = "Modified"
        
        # Cria arquivo primeiro
        test_file.write_text(original_content)
        
        # Edita arquivo
        file_ops.edit_file(test_file, new_content)
        
        assert test_file.read_text() == new_content
    
    def test_edit_nonexistent_file(self, file_ops, temp_dir):
        """Testa edição de arquivo inexistente"""
        test_file = temp_dir / "nonexistent.txt"
        
        with pytest.raises(FileOperationError) as exc_info:
            file_ops.edit_file(test_file, "content")
        
        assert "não existe" in str(exc_info.value)
    
    def test_append_to_file(self, file_ops, temp_dir):
        """Testa adição de conteúdo a arquivo"""
        test_file = temp_dir / "test.txt"
        original = "Line 1\n"
        append_text = "Line 2\n"
        
        test_file.write_text(original)
        file_ops.append_to_file(test_file, append_text)
        
        assert test_file.read_text() == original + append_text
    
    def test_delete_file(self, file_ops, temp_dir):
        """Testa deleção de arquivo"""
        test_file = temp_dir / "test.txt"
        test_file.write_text("To be deleted")
        
        file_ops.delete_file(test_file)
        
        assert not test_file.exists()
    
    def test_delete_nonexistent_file(self, file_ops, temp_dir):
        """Testa deleção de arquivo inexistente"""
        test_file = temp_dir / "nonexistent.txt"
        
        with pytest.raises(FileOperationError) as exc_info:
            file_ops.delete_file(test_file)
        
        assert "não existe" in str(exc_info.value)
    
    def test_read_file(self, file_ops, temp_dir):
        """Testa leitura de arquivo"""
        test_file = temp_dir / "test.txt"
        content = "Test content\nLine 2"
        test_file.write_text(content)
        
        read_content = file_ops.read_file(test_file)
        
        assert read_content == content
    
    def test_read_nonexistent_file(self, file_ops, temp_dir):
        """Testa leitura de arquivo inexistente"""
        test_file = temp_dir / "nonexistent.txt"
        
        with pytest.raises(FileOperationError) as exc_info:
            file_ops.read_file(test_file)
        
        assert "não existe" in str(exc_info.value)
    
    def test_list_files(self, file_ops, temp_dir):
        """Testa listagem de arquivos"""
        # Cria alguns arquivos
        (temp_dir / "file1.txt").write_text("content1")
        (temp_dir / "file2.py").write_text("content2")
        (temp_dir / "subdir").mkdir()
        (temp_dir / "subdir" / "file3.txt").write_text("content3")
        
        # Lista todos os arquivos
        all_files = file_ops.list_files(temp_dir)
        assert len(all_files) == 2  # Não inclui arquivos em subdiretórios
        
        # Lista apenas arquivos .txt
        txt_files = file_ops.list_files(temp_dir, "*.txt")
        assert len(txt_files) == 1
        assert txt_files[0].name == "file1.txt"
    
    def test_list_nonexistent_directory(self, file_ops):
        """Testa listagem de diretório inexistente"""
        with pytest.raises(FileOperationError) as exc_info:
            file_ops.list_files("/path/that/does/not/exist")
        
        assert "não existe" in str(exc_info.value)
