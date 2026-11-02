#### What's Fixed

- Fixed an Excel formula injection issue in the `Create XLSX File as Attachment From JSON Data` operation
  (`create_xslx_file_from_json_data`). Values beginning with `=` (e.g. `=1+1` or `=HYPERLINK(...)`) in the JSON
  data were automatically converted into executable XLSX formula elements by the XlsxWriter engine. The workbook
  is now written with `strings_to_formulas: false` (and `strings_to_urls: false`), so such values are stored as
  plain text cells instead of executable formulas or live hyperlinks.
- Fixed a path containment bypass in `check_file_traversal()`. The check previously used
  `os.path.commonprefix()`, which compares paths character by character rather than by path
  components, so sibling paths such as `/tmp-abc/...` were incorrectly accepted when `/tmp` is the
  allowed root. The check now uses `os.path.commonpath()` for a path-aware containment.
- Fixed a path traversal vulnerability in the `Create XLSX File as Attachment From JSON Data` operation (
  `create_xslx_file_from_json_data`). The user-supplied `fileName` was used to build the output file path without
  validation, allowing `../` sequences or an absolute path to write the XLSX file outside the intended `/tmp` directory.
  The constructed path is now checked with `check_file_traversal()` before the file is written, matching the protection
  already applied to `file_iri` in the `Extract Text` operation.
- Fixed a man-in-the-middle vulnerability in the Tika server JAR download (`_set_env`). The JAR was previously
  downloaded with TLS certificate verification disabled (`verify=False`). The download now verifies TLS, and the JAR's
  MD5 digest is checked against the official Apache Tika 2.9.4 checksum before it is executed. The JAR is also now
  staged as `/opt/cyops/configs/integrations/external_dependencies/tika-server.jar` (with its `.md5` sidecar) and
  `TIKA_SERVER_JAR`/`TIKA_PATH` are set before the `tika` library is imported, so python-tika runs the locally verified
  JAR instead of falling back to a plain-HTTP download from Maven Central into the world-writable `/tmp` directory.
  Air-gapped deployments can still pre-place the JAR or set `TIKA_SERVER_JAR`.
