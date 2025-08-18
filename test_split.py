#!/usr/bin/env python3
import asyncio
from message_utils import split_long_message

async def test_split():
    # Test with the actual message that got cut off
    test_message = """This server includes various tools primarily focused on server monitoring and management. Key tools commonly found include:

- **Checkmk**: Scalable monitoring with extensive plugins, real-time metrics, and alerting for CPU, memory, disk, etc.[1]

- **WhatsUp Gold**: IT infrastructure management with real-time performance insights and customizable dashboards.[1]

- **LibreNMS**: Open-source monitoring supporting diverse hardware and OS, with real-time health insights and customization.[1]

- **Datadog**: Full-stack monitoring with infrastructure, logs, APM, and over 450 integrations for cloud and physical servers.[2][3]

- **CloudPanel**: Free server control panel optimized for cloud hosting with monitoring, backups, SSL management, and multi-server support.[5]

- **PRTG**: Network and server monitoring with flexible notifications and real-time tracking (free tier available).[5]

Additionally, this server supports the Model Context Protocol (MCP) for exposing and invoking various AI capabilities and integrations. The MCP enables seamless communication between different tools and services, allowing for advanced automation and intelligent workflows.

Some more text to ensure we exceed the Discord limit and test the splitting functionality properly. This should trigger the message splitting logic and create multiple parts with proper [Part X/Y] indicators."""
    
    parts = await split_long_message(test_message)
    
    print(f"Message length: {len(test_message)} characters")
    print(f"Split into {len(parts)} parts\n")
    
    for i, part in enumerate(parts, 1):
        print(f"Part {i} ({len(part)} chars):")
        print("-" * 40)
        print(part[:200] + "..." if len(part) > 200 else part)
        print()

if __name__ == "__main__":
    asyncio.run(test_split())
