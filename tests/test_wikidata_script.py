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
        """Test that a successful API response returns a {qid: label} dict"""
        mock_response = Mock()
        mock_response.json.return_value = {
            'results': {
                'bindings': [
                    {
                        'item': {'value': 'http://www.wikidata.org/entity/Q1299'},
                        'itemLabel': {'value': 'The Beatles'},
                    },
                    {
                        'item': {'value': 'http://www.wikidata.org/entity/Q2306'},
                        'itemLabel': {'value': 'Pink Floyd'},
                    },
                    {
                        'item': {'value': 'http://www.wikidata.org/entity/Q2127'},
                        'itemLabel': {'value': 'Led Zeppelin'},
                    },
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

            # Verify results: dict keyed by Q-ID, labels preserved as-is
            assert bands == {
                'Q1299': 'The Beatles',
                'Q2306': 'Pink Floyd',
                'Q2127': 'Led Zeppelin',
            }

    def test_handles_missing_labels(self):
        """Test that entries missing either the item URI or itemLabel are skipped"""
        mock_response = Mock()
        mock_response.json.return_value = {
            'results': {
                'bindings': [
                    {
                        'item': {'value': 'http://www.wikidata.org/entity/Q7325'},
                        'itemLabel': {'value': 'Radiohead'},
                    },
                    {'item': {'value': 'http://www.wikidata.org/entity/Q12345'}},  # No label
                    {
                        'item': {'value': 'http://www.wikidata.org/entity/Q11365'},
                        'itemLabel': {'value': 'Nirvana'},
                    },
                ]
            }
        }
        mock_response.raise_for_status = Mock()

        with patch('requests.get', return_value=mock_response):
            bands = fetch_bands_from_wikidata()

            assert bands == {'Q7325': 'Radiohead', 'Q11365': 'Nirvana'}

    def test_handles_empty_results(self):
        """Test that empty results return an empty dict"""
        mock_response = Mock()
        mock_response.json.return_value = {
            'results': {
                'bindings': []
            }
        }
        mock_response.raise_for_status = Mock()

        with patch('requests.get', return_value=mock_response):
            bands = fetch_bands_from_wikidata()

            assert bands == {}

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

            # Should return an empty dict when structure is missing
            assert bands == {}

    def test_includes_entries_whose_label_looks_like_a_q_identifier(self):
        """Test that entries are not filtered out just because the label looks like a Q-ID

        Wikidata sometimes returns a Q-identifier as the label when no English
        label is available. Those entries should still be kept (the qid key is
        what matters for downstream merging)."""
        mock_response = Mock()
        mock_response.json.return_value = {
            'results': {
                'bindings': [
                    {
                        'item': {'value': 'http://www.wikidata.org/entity/Q158641'},
                        'itemLabel': {'value': 'Q158641'},  # Q-identifier as label
                    },
                    {
                        'item': {'value': 'http://www.wikidata.org/entity/Q1183633'},
                        'itemLabel': {'value': 'Destroyer'},
                    },
                ]
            }
        }
        mock_response.raise_for_status = Mock()

        with patch('requests.get', return_value=mock_response):
            bands = fetch_bands_from_wikidata()

            assert bands == {
                'Q158641': 'Q158641',
                'Q1183633': 'Destroyer',
            }
