---
title: Home
---

<div class="grid-left" markdown>

**IDMS** is a document management system that transforms your
physical documents into a searchable online archive so you can keep, well, _less paper_.

[Get started](setup.md){ .md-button .md-button--primary .index-callout }
[Demo](https://test-idms.impactai.ke){ .md-button .md-button--secondary target=\_blank }


</div>
<div class="clear"></div>

## Features

- **Organize and index** your scanned documents with tags, correspondents, types, and more.
- _Your_ data is stored locally on _your_ server and is never transmitted or shared in any way, unless you explicitly choose to do so.
- Performs **OCR** on your documents, adding searchable and selectable text, even to documents scanned with only images.
  - Utilizes the open-source Tesseract engine to recognize more than 100 languages.
  - _New!_ Supports remote OCR with Azure AI (opt-in).
- Documents are saved as PDF/A format which is designed for long term storage, alongside the unaltered originals.
- Uses machine-learning to automatically add tags, correspondents and document types to your documents.
- **New**: IDMS can now leverage AI (Large Language Models or LLMs) for document suggestions. This is an optional feature that can be enabled (and is disabled by default).
- Supports PDF documents, images, plain text files, Office documents (Word, Excel, PowerPoint, and LibreOffice equivalents)[^1] and more.
- IDMS stores your documents plain on disk. Filenames and folders are managed by IDMS and their format can be configured freely with different configurations assigned to different documents.
- **Beautiful, modern web application** that features:
  - Customizable dashboard with statistics.
  - Filtering by tags, correspondents, types, and more.
  - Bulk editing of tags, correspondents, types and more.
  - Drag-and-drop uploading of documents throughout the app.
  - Customizable views can be saved and displayed on the dashboard and / or sidebar.
  - Support for custom fields of various data types.
  - Shareable public links with optional expiration.
- **Full text search** helps you find what you need:
  - Auto completion suggests relevant words from your documents.
  - Results are sorted by relevance to your search query.
  - Highlighting shows you which parts of the document matched the query.
  - Searching for similar documents ("More like this")
- **Email processing**[^1]: import documents from your email accounts:
  - Configure multiple accounts and rules for each account.
  - After processing, IDMS can perform actions on the messages such as marking as read, deleting and more.
- A built-in robust **multi-user permissions** system that supports 'global' permissions as well as per document or object.
- A powerful workflow system that gives you even more control.
- **Optimized** for multi core systems: IDMS consumes multiple documents in parallel.
- The integrated sanity checker makes sure that your document archive is in good health.

[^1]: Office document and email consumption support is optional and provided by Apache Tika (see [configuration](https://docs.paperless-ngx.com/configuration/#tika))


## Scanners & Software

IDMS is compatible with many different scanners and scanning tools. A user-maintained list of scanners and other software is available on [the wiki](https://github.com/paperless-ngx/paperless-ngx/wiki/Scanner-&-Software-Recommendations).
