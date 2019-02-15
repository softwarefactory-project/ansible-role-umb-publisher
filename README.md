# umb-publisher

This role publishes UMB message:

```yaml
- hosts: localhost
  roles:
    - name: umb-publisher
      umb_urls:
        - amqps://broker01.example.com
        - amqps://broker02.example.com
      umb_address: /topic/VirtualTopic.qe.ci.zuul
      umb_body:
        build: os-release-4243
        arch: x86_64
        hash: sha256://...
```
