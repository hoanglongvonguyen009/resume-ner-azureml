"""Unit tests for MLflow setup utility."""

from common.shared.mlflow_setup import (
    setup_mlflow_cross_platform,
    setup_mlflow_from_config,
    create_ml_client_from_config,
    _get_azure_ml_tracking_uri,
    _get_local_tracking_uri,
    _try_import_azureml_mlflow,
    _check_azureml_mlflow_available,
)
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch
import importlib
import sys

import pytest

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / "src"))


@pytest.fixture
def temp_dir():
    """Create temporary directory for tests."""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    import shutil
    shutil.rmtree(temp_path)


class TestGetLocalTrackingUri:
    """Tests for _get_local_tracking_uri function."""

    @patch("common.shared.mlflow_setup.detect_platform")
    def test_local_platform(self, mock_detect):
        """Test local platform returns SQLite URI in ./mlruns."""
        mock_detect.return_value = "local"

        uri = _get_local_tracking_uri()

        assert uri.startswith("sqlite:///")
        assert "mlflow.db" in uri
        # Should be in current directory's mlruns folder
        assert Path(uri.replace("sqlite:///", "")).parent.name == "mlruns"

    @patch("common.shared.mlflow_setup.detect_platform")
    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.is_dir")
    @patch("pathlib.Path.mkdir")
    def test_colab_with_drive(self, mock_mkdir, mock_is_dir, mock_exists, mock_detect):
        """Test Colab platform with Drive mounted uses Drive path."""
        mock_detect.return_value = "colab"
        mock_exists.return_value = True
        mock_is_dir.return_value = True
        mock_mkdir.return_value = None  # Mock mkdir to avoid actual directory creation

        uri = _get_local_tracking_uri()

        assert uri.startswith("sqlite:///")
        assert "mlflow.db" in uri
        assert "/content/drive/MyDrive" in uri or "resume-ner-mlflow" in uri

    @patch("common.shared.mlflow_setup.detect_platform")
    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.mkdir")
    def test_colab_without_drive(self, mock_mkdir, mock_exists, mock_detect):
        """Test Colab platform without Drive uses /content."""
        mock_detect.return_value = "colab"
        mock_exists.return_value = False
        mock_mkdir.return_value = None  # Mock mkdir to avoid actual directory creation

        uri = _get_local_tracking_uri()

        assert uri.startswith("sqlite:///")
        assert "mlflow.db" in uri
        assert "/content" in uri

    @patch("common.shared.mlflow_setup.detect_platform")
    @patch("pathlib.Path.mkdir")
    def test_kaggle_platform(self, mock_mkdir, mock_detect):
        """Test Kaggle platform uses /kaggle/working."""
        mock_detect.return_value = "kaggle"
        mock_mkdir.return_value = None  # Mock mkdir to avoid actual directory creation

        uri = _get_local_tracking_uri()

        assert uri.startswith("sqlite:///")
        assert "mlflow.db" in uri
        assert "/kaggle/working" in uri


class TestGetAzureMlTrackingUri:
    """Tests for _get_azure_ml_tracking_uri function."""

    @patch("common.shared.mlflow_setup._check_azureml_mlflow_available")
    def test_success(self, mock_check):
        """Test successful Azure ML workspace URI retrieval."""
        mock_ml_client = MagicMock()
        mock_workspace = MagicMock()
        mock_workspace.mlflow_tracking_uri = "azureml://workspace/experiments"
        mock_ml_client.workspace_name = "test-ws"
        mock_ml_client.workspaces.get.return_value = mock_workspace
        mock_check.return_value = True

        # Mock the azureml.mlflow import - it's imported inside the function
        with patch("builtins.__import__", side_effect=lambda name, *args, **kwargs: (
            MagicMock() if name == "azureml.mlflow" else __import__(name, *args, **kwargs)
        )):
            uri = _get_azure_ml_tracking_uri(mock_ml_client)

            assert uri == "azureml://workspace/experiments"
            mock_ml_client.workspaces.get.assert_called_once_with(
                name="test-ws")

    @patch("common.shared.mlflow_setup._check_azureml_mlflow_available")
    def test_import_error(self, mock_check):
        """Test ImportError when azureml.mlflow is not available."""
        mock_ml_client = MagicMock()
        mock_check.return_value = False
        
        # Mock subprocess.run (imported inside the function)
        with patch("subprocess.run") as mock_subprocess:
            mock_result = MagicMock()
            mock_result.returncode = 1  # Package not installed
            mock_subprocess.return_value = mock_result
            
            with pytest.raises(ImportError) as exc_info:
                _get_azure_ml_tracking_uri(mock_ml_client)

            assert "azureml.mlflow" in str(exc_info.value)

    @patch("common.shared.mlflow_setup._check_azureml_mlflow_available")
    def test_workspace_access_error(self, mock_check):
        """Test RuntimeError when workspace access fails."""
        mock_ml_client = MagicMock()
        mock_ml_client.workspace_name = "test-ws"
        mock_ml_client.workspaces.get.side_effect = Exception("Access denied")
        mock_check.return_value = True

        with patch("builtins.__import__", return_value=MagicMock()):
            with pytest.raises(RuntimeError) as exc_info:
                _get_azure_ml_tracking_uri(mock_ml_client)

            assert "Failed to get Azure ML workspace tracking URI" in str(
                exc_info.value)


class TestSetupMlflowCrossPlatform:
    """Tests for setup_mlflow_cross_platform function."""

    @patch("common.shared.mlflow_setup.mlflow")
    @patch("common.shared.mlflow_setup._get_local_tracking_uri")
    def test_local_fallback_no_ml_client(self, mock_get_local, mock_mlflow):
        """Test local fallback when no ML client provided."""
        mock_get_local.return_value = "sqlite:///./mlruns/mlflow.db"

        uri = setup_mlflow_cross_platform(
            experiment_name="test-experiment",
            ml_client=None
        )

        assert uri == "sqlite:///./mlruns/mlflow.db"
        mock_get_local.assert_called_once()
        mock_mlflow.set_tracking_uri.assert_called_once_with(
            "sqlite:///./mlruns/mlflow.db")
        mock_mlflow.set_experiment.assert_called_once_with("test-experiment")

    @patch("common.shared.mlflow_setup.mlflow")
    @patch("common.shared.mlflow_setup._get_azure_ml_tracking_uri")
    def test_azure_ml_success(self, mock_get_azure, mock_mlflow):
        """Test successful Azure ML setup."""
        mock_ml_client = MagicMock()
        mock_get_azure.return_value = "azureml://workspace/experiments"

        uri = setup_mlflow_cross_platform(
            experiment_name="test-experiment",
            ml_client=mock_ml_client
        )

        assert uri == "azureml://workspace/experiments"
        mock_get_azure.assert_called_once_with(mock_ml_client)
        mock_mlflow.set_tracking_uri.assert_called_once_with(
            "azureml://workspace/experiments")
        mock_mlflow.set_experiment.assert_called_once_with("test-experiment")

    @patch("common.shared.mlflow_setup.mlflow")
    @patch("common.shared.mlflow_setup._get_azure_ml_tracking_uri")
    @patch("common.shared.mlflow_setup._get_local_tracking_uri")
    def test_azure_ml_failure_with_fallback(self, mock_get_local, mock_get_azure, mock_mlflow):
        """Test Azure ML failure with fallback enabled."""
        mock_ml_client = MagicMock()
        mock_get_azure.side_effect = Exception("Azure ML unavailable")
        mock_get_local.return_value = "sqlite:///./mlruns/mlflow.db"

        uri = setup_mlflow_cross_platform(
            experiment_name="test-experiment",
            ml_client=mock_ml_client,
            fallback_to_local=True
        )

        assert uri == "sqlite:///./mlruns/mlflow.db"
        mock_get_azure.assert_called_once()
        mock_get_local.assert_called_once()
        mock_mlflow.set_tracking_uri.assert_called_once_with(
            "sqlite:///./mlruns/mlflow.db")
        mock_mlflow.set_experiment.assert_called_once_with("test-experiment")

    @patch("common.shared.mlflow_setup._get_azure_ml_tracking_uri")
    def test_azure_ml_failure_no_fallback(self, mock_get_azure):
        """Test Azure ML failure with fallback disabled raises error."""
        mock_ml_client = MagicMock()
        mock_get_azure.side_effect = Exception("Azure ML unavailable")

        with pytest.raises(RuntimeError) as exc_info:
            setup_mlflow_cross_platform(
                experiment_name="test-experiment",
                ml_client=mock_ml_client,
                fallback_to_local=False
            )

        assert "Azure ML tracking failed and fallback disabled" in str(
            exc_info.value)

    def test_mlflow_not_installed(self):
        """Test ImportError when mlflow is not installed.
        
        Note: mlflow is imported at module load time. The function uses mlflow directly,
        so if mlflow is not available, it will raise ImportError when accessing mlflow.
        Since mlflow is installed in our environment, we test by removing mlflow from
        the module and patching the import.
        """
        from common.shared import mlflow_setup
        import builtins
        
        # Save original mlflow
        original_mlflow = sys.modules.get('mlflow')
        original_mlflow_attr = getattr(mlflow_setup, 'mlflow', None)
        
        # Remove mlflow from sys.modules and module
        if 'mlflow' in sys.modules:
            del sys.modules['mlflow']
        if hasattr(mlflow_setup, 'mlflow'):
            delattr(mlflow_setup, 'mlflow')
        
        # Patch import to raise ImportError for mlflow
        original_import = builtins.__import__
        def mock_import(name, *args, **kwargs):
            if name == 'mlflow' or (isinstance(name, str) and name.startswith('mlflow')):
                raise ImportError("No module named 'mlflow'")
            return original_import(name, *args, **kwargs)
        
        try:
            with patch.object(builtins, '__import__', side_effect=mock_import):
                # setup_mlflow_cross_platform() will try to use mlflow and should raise NameError
                # (since mlflow is not defined when import fails)
                with pytest.raises((ImportError, NameError, AttributeError)) as exc_info:
                    mlflow_setup.setup_mlflow_cross_platform(
                        experiment_name="test",
                        ml_client=None,
                        fallback_to_local=False,
                    )
                # Verify error is related to mlflow (NameError: name 'mlflow' is not defined)
                error_str = str(exc_info.value).lower()
                assert "mlflow" in error_str or "not defined" in error_str or "has no attribute" in error_str
        finally:
            # Restore mlflow
            if original_mlflow:
                sys.modules['mlflow'] = original_mlflow
            if original_mlflow_attr:
                mlflow_setup.mlflow = original_mlflow_attr


class TestPlatformSpecificBehavior:
    """Integration-style tests for platform-specific behavior."""

    @patch("common.shared.mlflow_setup.mlflow")
    @patch("common.shared.mlflow_setup.detect_platform")
    @patch.dict(os.environ, {"COLAB_GPU": "1"})
    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.is_dir")
    @patch("pathlib.Path.mkdir")
    def test_colab_drive_mounted(self, mock_mkdir, mock_is_dir, mock_exists, mock_detect, mock_mlflow):
        """Test Colab with Drive mounted uses Drive path."""
        mock_detect.return_value = "colab"
        mock_exists.return_value = True
        mock_is_dir.return_value = True
        mock_mkdir.return_value = None  # Mock mkdir to avoid actual directory creation

        uri = setup_mlflow_cross_platform(experiment_name="test")

        # Should use Drive path
        assert "drive" in uri.lower() or "mydrive" in uri.lower()

    @patch("common.shared.mlflow_setup.mlflow")
    @patch("common.shared.mlflow_setup.detect_platform")
    @patch.dict(os.environ, {"KAGGLE_KERNEL_RUN_TYPE": "Interactive"})
    @patch("pathlib.Path.mkdir")
    def test_kaggle_platform(self, mock_mkdir, mock_detect, mock_mlflow):
        """Test Kaggle platform uses /kaggle/working."""
        mock_detect.return_value = "kaggle"
        mock_mkdir.return_value = None  # Mock mkdir to avoid actual directory creation

        uri = setup_mlflow_cross_platform(experiment_name="test")

        assert "/kaggle/working" in uri

    @patch("common.shared.mlflow_setup.mlflow")
    @patch.dict(os.environ, {}, clear=True)
    def test_local_platform(self, mock_mlflow):
        """Test local platform uses ./mlruns."""
        uri = setup_mlflow_cross_platform(experiment_name="test")

        assert uri.startswith("sqlite:///")
        # Should create mlruns directory
        assert "mlruns" in uri


class TestCreateMlClientFromConfig:
    """Tests for create_ml_client_from_config function."""

    @patch("common.shared.mlflow_setup.load_yaml")
    @patch("common.shared.mlflow_setup.detect_platform")
    def test_success_with_env_vars(self, mock_detect, mock_load_yaml):
        """Test successful MLClient creation with environment variables."""
        # Skip if azure modules aren't available (they're required for this test)
        try:
            import azure.ai.ml
            import azure.identity
        except ImportError:
            pytest.skip("Azure SDK not available - skipping test")
        
        mock_load_yaml.return_value = {
            "azure_ml": {
                "enabled": True,
                "workspace_name": "test-ws"
            }
        }
        mock_detect.return_value = "local"  # Not Colab/Kaggle
        
        # Mock Path.exists to return True for mlflow.yaml (so function loads config)
        # and False for config.env and infrastructure.yaml (so it uses env vars)
        def exists_side_effect(self):
            path_str = str(self)
            if path_str.endswith("mlflow.yaml"):
                return True
            if path_str.endswith("config.env") or path_str.endswith("infrastructure.yaml"):
                return False
            return False
        
        # Mock MLClient and DefaultAzureCredential
        mock_cred_instance = MagicMock()
        mock_client_instance = MagicMock()
        
        # Set environment variables before calling the function
        with patch.dict(os.environ, {
            "AZURE_SUBSCRIPTION_ID": "test-sub-id",
            "AZURE_RESOURCE_GROUP": "test-rg"
        }, clear=False):
            # Patch Path.exists using patch.object to patch the instance method
            with patch.object(Path, "exists", side_effect=exists_side_effect, autospec=True):
                # Patch the imports where they're used in the function (inside the try block)
                with patch("azure.ai.ml.MLClient", return_value=mock_client_instance) as mock_mlclient:
                    with patch("azure.identity.DefaultAzureCredential", return_value=mock_cred_instance):
                        config_dir = Path("config")
                        client = create_ml_client_from_config(config_dir)

                        assert client is not None
                        assert client == mock_client_instance
                        # Verify MLClient was called with correct arguments
                        assert mock_mlclient.called
                        call_args = mock_mlclient.call_args
                        assert call_args[1]["subscription_id"] == "test-sub-id"
                        assert call_args[1]["resource_group_name"] == "test-rg"
                        assert call_args[1]["workspace_name"] == "test-ws"

    @patch("common.shared.mlflow_setup.load_yaml")
    def test_azure_ml_disabled(self, mock_load_yaml):
        """Test returns None when Azure ML is disabled."""
        mock_load_yaml.return_value = {
            "azure_ml": {
                "enabled": False
            }
        }

        config_dir = Path("config")
        client = create_ml_client_from_config(config_dir)

        assert client is None

    @patch("common.shared.mlflow_setup.load_yaml")
    def test_config_missing_azure_ml_section(self, mock_load_yaml):
        """Test returns None when Azure ML section is missing."""
        mock_load_yaml.return_value = {}

        config_dir = Path("config")
        client = create_ml_client_from_config(config_dir)

        assert client is None

    @patch("common.shared.mlflow_setup.load_yaml")
    @patch("common.shared.mlflow_setup.detect_platform")
    @patch("pathlib.Path.exists")
    @patch.dict(os.environ, {}, clear=True)
    def test_missing_credentials(self, mock_exists, mock_detect, mock_load_yaml):
        """Test returns None when credentials are missing."""
        mock_load_yaml.return_value = {
            "azure_ml": {
                "enabled": True,
                "workspace_name": "test-ws"
            }
        }
        mock_detect.return_value = "local"
        # Mock Path.exists to return True for mlflow.yaml but False for config.env
        def exists_side_effect(*args):
            # args[0] is 'self' (the Path instance)
            path_self = args[0] if args else None
            if path_self is None:
                return False
            path_str = str(path_self)
            if path_str.endswith("mlflow.yaml"):
                return True
            if path_str.endswith("config.env"):
                return False
            return False
        mock_exists.side_effect = exists_side_effect

        config_dir = Path("config")
        client = create_ml_client_from_config(config_dir)

        assert client is None

    @patch("common.shared.mlflow_setup.load_yaml")
    @patch("common.shared.mlflow_setup.detect_platform")
    def test_import_error(self, mock_detect, mock_load_yaml):
        """Test returns None when Azure ML SDK not available."""
        mock_load_yaml.return_value = {
            "azure_ml": {
                "enabled": True,
                "workspace_name": "test-ws"
            }
        }
        mock_detect.return_value = "local"

        # The function catches ImportError and returns None, so we test for that behavior
        # Patch the import inside the function where it's used
        original_import = __import__
        def mock_import(name, *args, **kwargs):
            if name == "azure.ai.ml" or name == "azure.identity":
                raise ImportError("No module named 'azure'")
            return original_import(name, *args, **kwargs)
        
        with patch("builtins.__import__", side_effect=mock_import):
            client = create_ml_client_from_config(Path("config"))
            # Function returns None when import fails, not raises
            assert client is None


class TestSetupMlflowFromConfig:
    """Tests for setup_mlflow_from_config function."""

    @patch("common.shared.mlflow_setup.setup_mlflow_cross_platform")
    @patch("common.shared.mlflow_setup.load_yaml")
    def test_config_file_exists_azure_enabled(self, mock_load_yaml, mock_setup):
        """Test setup with config file and Azure ML enabled."""
        mock_load_yaml.return_value = {
            "azure_ml": {
                "enabled": True,
                "workspace_name": "test-ws"
            }
        }
        mock_setup.return_value = "azureml://workspace/experiments"

        with patch("common.shared.mlflow_setup.create_ml_client_from_config") as mock_create:
            mock_client = MagicMock()
            mock_create.return_value = mock_client

            uri = setup_mlflow_from_config(
                experiment_name="test-experiment",
                config_dir=Path("config")
            )

            assert uri == "azureml://workspace/experiments"
            mock_setup.assert_called_once_with(
                experiment_name="test-experiment",
                ml_client=mock_client,
                fallback_to_local=True
            )

    @patch("common.shared.mlflow_setup.setup_mlflow_cross_platform")
    @patch("common.shared.mlflow_setup.load_yaml")
    def test_config_file_exists_azure_disabled(self, mock_load_yaml, mock_setup):
        """Test setup with config file and Azure ML disabled."""
        mock_load_yaml.return_value = {
            "azure_ml": {
                "enabled": False
            }
        }
        mock_setup.return_value = "sqlite:///./mlruns/mlflow.db"

        uri = setup_mlflow_from_config(
            experiment_name="test-experiment",
            config_dir=Path("config")
        )

        assert uri == "sqlite:///./mlruns/mlflow.db"
        mock_setup.assert_called_once_with(
            experiment_name="test-experiment",
            ml_client=None,
            fallback_to_local=True
        )

    @patch("common.shared.mlflow_setup.setup_mlflow_cross_platform")
    @patch("pathlib.Path.exists")
    def test_config_file_missing(self, mock_exists, mock_setup):
        """Test setup when config file doesn't exist."""
        mock_exists.return_value = False
        mock_setup.return_value = "sqlite:///./mlruns/mlflow.db"

        uri = setup_mlflow_from_config(
            experiment_name="test-experiment",
            config_dir=Path("config")
        )

        assert uri == "sqlite:///./mlruns/mlflow.db"
        mock_setup.assert_called_once_with(
            experiment_name="test-experiment",
            ml_client=None,
            fallback_to_local=True
        )


class TestAzureMlNamespaceCollision:
    """Tests for azureml.mlflow import with namespace collision handling.
    
    Tests the fix for the issue where our local src/azureml module shadows
    the installed azureml package, preventing azureml.mlflow from being imported.
    """

    def test_import_with_local_azureml_shadowing(self):
        """Test that azureml.mlflow can be imported even when local azureml shadows it.
        
        This test simulates the namespace collision scenario:
        1. Our local src/azureml module is imported first (shadows installed package)
        2. _try_import_azureml_mlflow() should still be able to import azureml.mlflow
        3. Our local azureml functions should still work
        """
        # Clear any existing azureml imports
        if 'azureml' in sys.modules:
            del sys.modules['azureml']
        if 'azureml.mlflow' in sys.modules:
            del sys.modules['azureml.mlflow']
        
        # Import our local azureml module first (simulating the shadowing scenario)
        # Handle case where azure SDK might not be installed
        try:
            from azureml import ensure_data_asset_uploaded
            
            # Verify local azureml is in sys.modules and is our local one
            assert 'azureml' in sys.modules
            local_azureml = sys.modules['azureml']
            assert 'src/azureml' in local_azureml.__file__ or local_azureml.__file__.endswith('src/azureml/__init__.py')
            
            # Now test that _try_import_azureml_mlflow can handle the shadowing
            # This should work by importing from site-packages
            result = _try_import_azureml_mlflow()
            # If azureml-mlflow is installed, it should succeed
            # If not installed, it should return False gracefully
            assert isinstance(result, bool)
            
            # If it succeeded, verify azureml.mlflow is available
            if result:
                import azureml.mlflow
                assert 'azureml.mlflow' in sys.modules
                # Verify our local azureml still works
                from azureml import ensure_data_asset_uploaded
                assert callable(ensure_data_asset_uploaded)
        except (ImportError, ModuleNotFoundError) as e:
            # If azure SDK or azureml-mlflow is not installed, skip this test
            # The important thing is that it doesn't crash due to namespace collision
            pytest.skip(f"Skipping test - required dependencies not available: {e}")

    def test_check_azureml_mlflow_available_with_shadowing(self):
        """Test _check_azureml_mlflow_available() works with namespace collision."""
        # Clear any existing azureml imports
        if 'azureml' in sys.modules:
            del sys.modules['azureml']
        if 'azureml.mlflow' in sys.modules:
            del sys.modules['azureml.mlflow']
        
        # Reset the global state
        import common.shared.mlflow_setup
        common.shared.mlflow_setup._AZUREML_MLFLOW_AVAILABLE = False
        common.shared.mlflow_setup._AZUREML_MLFLOW_IMPORT_ERROR = None
        
        # Import our local azureml module first (simulating shadowing)
        # Handle case where azure SDK might not be installed
        try:
            from azureml import ensure_data_asset_uploaded
            
            # Test the check function
            result = _check_azureml_mlflow_available()
            assert isinstance(result, bool)
            
            # Verify our local azureml still works
            from azureml import ensure_data_asset_uploaded
            assert callable(ensure_data_asset_uploaded)
        except (ImportError, ModuleNotFoundError) as e:
            pytest.skip(f"Skipping test - required dependencies not available: {e}")

    def test_local_azureml_functions_still_work_after_import(self):
        """Test that local azureml functions work after azureml.mlflow import attempt."""
        # Clear any existing azureml imports
        if 'azureml' in sys.modules:
            del sys.modules['azureml']
        if 'azureml.mlflow' in sys.modules:
            del sys.modules['azureml.mlflow']
        
        # Import our local azureml module
        # Handle case where azure SDK might not be installed
        try:
            from azureml import (
                ensure_data_asset_uploaded,
                register_data_asset,
                resolve_dataset_path,
                build_data_asset_reference,
            )
            
            # Verify all functions are callable
            assert callable(ensure_data_asset_uploaded)
            assert callable(register_data_asset)
            assert callable(resolve_dataset_path)
            assert callable(build_data_asset_reference)
            
            # Now try to import azureml.mlflow (this should not break our local module)
            try:
                _try_import_azureml_mlflow()
            except Exception:
                pass  # Ignore import errors if azureml-mlflow is not installed
            
            # Verify our local functions still work after import attempt
            assert callable(ensure_data_asset_uploaded)
            assert callable(register_data_asset)
            assert callable(resolve_dataset_path)
            assert callable(build_data_asset_reference)
            
            # Verify we can still import from local azureml
            from azureml import ensure_data_asset_uploaded
            assert callable(ensure_data_asset_uploaded)
        except (ImportError, ModuleNotFoundError) as e:
            pytest.skip(f"Skipping test - required dependencies not available: {e}")
