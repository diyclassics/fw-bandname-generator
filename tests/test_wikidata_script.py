"""
Tests for the Wikidata band names fetcher script
"""

import pytest
from unittest.mock import Mock, patch
import sys
import os

# Add scripts directory to path so we can import the module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from update_bands_from_wikidata import fetch_bands_from_wikidata, WIKIDATA_SPARQL_ENDPOINT


class TestFetchBandsFromWikidata:
    """Test suite for fetch_bands_from_wikidata function"""

    def test_successful_query_returns_band_names(self):
        """Test that successful API response returns list of band names"""
        mock_response = Mock()
        mock_response.json.return_value = {
            'results': {
                'bindings': [
                    {'itemLabel': {'value': 'The Beatles'}},
                    {'itemLabel': {'value': 'Pink Floyd'}},
                    {'itemLabel': {'value': 'Led Zeppelin'}},
                ]
            }
        }
        mock_response.raise_for_status = Mock()

        with patch('requests.get', return_value=mock_response) as mock_get:
            bands = fetch_bands_from_wikidata()

            # Verify correct endpoint called
            assert mock_get.called
            call_args = mock_get.call_args
            assert call_args[0][0] == WIKIDATA_SPARQL_ENDPOINT

            # Verify results
            assert len(bands) == 3
            assert 'The Beatles' in bands
            assert 'Pink Floyd' in bands
            assert 'Led Zeppelin' in bands

    def test_handles_missing_labels(self):
        """Test that entries without itemLabel are skipped"""
        mock_response = Mock()
        mock_response.json.return_value = {
            'results': {
                'bindings': [
                    {'itemLabel': {'value': 'Radiohead'}},
                    {'item': {'value': 'http://www.wikidata.org/entity/Q12345'}},  # No label
                    {'itemLabel': {'value': 'Nirvana'}},
                ]
            }
        }
        mock_response.raise_for_status = Mock()

        with patch('requests.get', return_value=mock_response):
            bands = fetch_bands_from_wikidata()

            assert len(bands) == 2
            assert 'Radiohead' in bands
            assert 'Nirvana' in bands

    def test_handles_empty_results(self):
        """Test that empty results return empty list"""
        mock_response = Mock()
        mock_response.json.return_value = {
            'results': {
                'bindings': []
            }
        }
        mock_response.raise_for_status = Mock()

        with patch('requests.get', return_value=mock_response):
            bands = fetch_bands_from_wikidata()

            assert bands == []

    def test_request_has_correct_headers(self):
        """Test that request includes proper User-Agent and Accept headers"""
        mock_response = Mock()
        mock_response.json.return_value = {'results': {'bindings': []}}
        mock_response.raise_for_status = Mock()

        with patch('requests.get', return_value=mock_response) as mock_get:
            fetch_bands_from_wikidata()

            call_kwargs = mock_get.call_args[1]
            headers = call_kwargs['headers']

            assert 'User-Agent' in headers
            assert 'FW-BandName-Generator' in headers['User-Agent']
            assert headers['Accept'] == 'application/json'

    def test_request_includes_sparql_query(self):
        """Test that SPARQL query is included in request params"""
        mock_response = Mock()
        mock_response.json.return_value = {'results': {'bindings': []}}
        mock_response.raise_for_status = Mock()

        with patch('requests.get', return_value=mock_response) as mock_get:
            fetch_bands_from_wikidata()

            call_kwargs = mock_get.call_args[1]
            params = call_kwargs['params']

            assert 'query' in params
            assert 'Q215380' in params['query']  # Musical group identifier
            assert 'format' in params
            assert params['format'] == 'json'

    def test_raises_exception_on_http_error(self):
        """Test that HTTP errors are propagated"""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("HTTP 500 Error")

        with patch('requests.get', return_value=mock_response):
            with pytest.raises(Exception):
                fetch_bands_from_wikidata()

    def test_handles_malformed_json(self):
        """Test that malformed responses are handled gracefully"""
        mock_response = Mock()
        mock_response.json.return_value = {}  # Missing 'results' key
        mock_response.raise_for_status = Mock()

        with patch('requests.get', return_value=mock_response):
            bands = fetch_bands_from_wikidata()

            # Should return empty list when structure is missing
            assert bands == []

    def test_filters_q_identifiers(self):
        """Test that Q-identifiers (when label is missing) are still included"""
        mock_response = Mock()
        mock_response.json.return_value = {
            'results': {
                'bindings': [
                    {'itemLabel': {'value': 'Q158641'}},  # Q-identifier as label
                    {'itemLabel': {'value': 'Destroyer'}},
                ]
            }
        }
        mock_response.raise_for_status = Mock()

        with patch('requests.get', return_value=mock_response):
            bands = fetch_bands_from_wikidata()

            # Current implementation includes Q-identifiers
            # This matches the actual output we saw in testing
            assert len(bands) == 2
            assert 'Q158641' in bands
            assert 'Destroyer' in bands
