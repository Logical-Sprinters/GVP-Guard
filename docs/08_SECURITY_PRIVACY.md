# Security, Privacy and Responsible AI

## Principles
- Human decision before enforcement
- Minimum necessary data
- Least-privilege access
- Short, configurable retention
- Traceable decisions
- Clear uncertainty

## Threats
Unauthorized evidence access, tampering, leaked stream credentials, insecure uploads, malicious files, ID enumeration, over-retention and model bias.

## Controls
- Authentication and role-based authorization
- TLS and encrypted secrets
- Signed evidence URLs
- File type/size validation and malware scanning
- UUID identifiers and rate limits
- Audit log of views and changes
- Configurable retention/deletion jobs
- Backup and restore tests
- Stream credentials outside source code

## Responsible AI controls
- No automatic fines
- No face recognition
- Manual review for ambiguous events/plates
- Store trigger reasons and model version
- Monitor false alerts by camera/lighting
- Provide appeal/correction path through official process

## Evidence integrity
Checksums may be added later, but do not claim legal chain of custody until the complete capture, identity, retention and audit process is formally implemented and reviewed.

## Privacy review questions
Who can view clips? How long are they retained? What happens to rejected incidents? Can unrelated faces be blurred? Who authorizes camera and registry access?
