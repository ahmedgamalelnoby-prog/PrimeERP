        fragments = backend_fragments.get(contract, (contract,))
        # Router declarations/decorators are often formatted across multiple
        # lines. Compare a whitespace-normalized representation so the audit
        # validates the actual contract instead of a particular formatter.
        backend_text = re.sub(r"\\s+", " ", read(backend_file)).strip()
        normalized_fragments = [re.sub(r"\\s+", " ", fragment).strip() for fragment in fragments]
        if not all(fragment in backend_text for fragment in normalized_fragments):
            raise SystemExit(f"Backend contract not found: {contract} in {backend_file.relative_to(ROOT)}")
