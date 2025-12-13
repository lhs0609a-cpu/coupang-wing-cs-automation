"""
Port Management Router
포트 관리 및 자동 할당 API
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List
import socket
import psutil
from loguru import logger

router = APIRouter(tags=["Port Management"])


class PortCheckRequest(BaseModel):
    port: int


class PortCheckResponse(BaseModel):
    port: int
    available: bool
    in_use: bool
    process_name: Optional[str] = None
    process_pid: Optional[int] = None


class PortRangeRequest(BaseModel):
    start_port: int = 8000
    end_port: int = 8010
    count: int = 1


def is_port_in_use(port: int) -> tuple[bool, Optional[str], Optional[int]]:
    """
    포트가 사용 중인지 확인
    Returns: (in_use, process_name, pid)
    """
    try:
        # 소켓으로 포트 사용 여부 확인
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            result = s.connect_ex(('localhost', port))

            if result == 0:
                # 포트가 사용 중 - 프로세스 정보 찾기
                for conn in psutil.net_connections():
                    if conn.laddr.port == port and conn.status == 'LISTEN':
                        try:
                            proc = psutil.Process(conn.pid)
                            return True, proc.name(), conn.pid
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            return True, None, None
                return True, None, None
            else:
                return False, None, None
    except Exception as e:
        logger.error(f"포트 {port} 확인 중 오류: {str(e)}")
        return False, None, None


def find_available_ports(start_port: int, end_port: int, count: int = 1) -> List[int]:
    """
    사용 가능한 포트 목록 찾기
    """
    available_ports = []

    for port in range(start_port, end_port + 1):
        if len(available_ports) >= count:
            break

        in_use, _, _ = is_port_in_use(port)
        if not in_use:
            available_ports.append(port)

    return available_ports


def kill_process_on_port(port: int) -> bool:
    """
    특정 포트를 사용하는 프로세스 종료
    """
    try:
        for conn in psutil.net_connections():
            if conn.laddr.port == port and conn.status == 'LISTEN':
                try:
                    proc = psutil.Process(conn.pid)
                    proc.terminate()
                    proc.wait(timeout=5)
                    logger.info(f"포트 {port}의 프로세스 {proc.name()} (PID: {conn.pid}) 종료됨")
                    return True
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired) as e:
                    logger.error(f"프로세스 종료 실패: {str(e)}")
                    return False
        return False
    except Exception as e:
        logger.error(f"포트 {port}의 프로세스 종료 중 오류: {str(e)}")
        return False


@router.get("/port/check/{port}")
async def check_port(port: int):
    """
    특정 포트의 사용 여부 확인
    """
    if port < 1 or port > 65535:
        raise HTTPException(status_code=400, detail="유효하지 않은 포트 번호입니다")

    in_use, process_name, pid = is_port_in_use(port)

    return PortCheckResponse(
        port=port,
        available=not in_use,
        in_use=in_use,
        process_name=process_name,
        process_pid=pid
    )


@router.post("/port/find-available")
async def find_available(request: PortRangeRequest):
    """
    사용 가능한 포트 찾기
    """
    if request.start_port < 1 or request.end_port > 65535:
        raise HTTPException(status_code=400, detail="유효하지 않은 포트 범위입니다")

    if request.start_port > request.end_port:
        raise HTTPException(status_code=400, detail="시작 포트가 종료 포트보다 큽니다")

    available_ports = find_available_ports(
        request.start_port,
        request.end_port,
        request.count
    )

    return {
        "success": True,
        "count": len(available_ports),
        "ports": available_ports
    }


@router.post("/port/kill/{port}")
async def kill_port(port: int):
    """
    특정 포트를 사용하는 프로세스 종료
    """
    if port < 1 or port > 65535:
        raise HTTPException(status_code=400, detail="유효하지 않은 포트 번호입니다")

    in_use, process_name, pid = is_port_in_use(port)

    if not in_use:
        return {
            "success": False,
            "message": f"포트 {port}는 사용 중이지 않습니다"
        }

    success = kill_process_on_port(port)

    if success:
        return {
            "success": True,
            "message": f"포트 {port}의 프로세스를 종료했습니다",
            "port": port,
            "process_name": process_name,
            "pid": pid
        }
    else:
        return {
            "success": False,
            "message": f"포트 {port}의 프로세스 종료에 실패했습니다"
        }


@router.post("/port/clear-range")
async def clear_port_range(request: PortRangeRequest):
    """
    포트 범위 내의 모든 프로세스 종료
    """
    if request.start_port < 1 or request.end_port > 65535:
        raise HTTPException(status_code=400, detail="유효하지 않은 포트 범위입니다")

    killed_ports = []
    failed_ports = []

    for port in range(request.start_port, request.end_port + 1):
        in_use, process_name, pid = is_port_in_use(port)

        if in_use:
            success = kill_process_on_port(port)
            if success:
                killed_ports.append({
                    "port": port,
                    "process_name": process_name,
                    "pid": pid
                })
            else:
                failed_ports.append({
                    "port": port,
                    "process_name": process_name,
                    "pid": pid
                })

    return {
        "success": len(failed_ports) == 0,
        "killed_count": len(killed_ports),
        "failed_count": len(failed_ports),
        "killed_ports": killed_ports,
        "failed_ports": failed_ports
    }


@router.get("/port/list-active")
async def list_active_ports():
    """
    현재 활성화된 모든 포트 목록
    """
    active_ports = []

    try:
        for conn in psutil.net_connections():
            if conn.status == 'LISTEN':
                try:
                    proc = psutil.Process(conn.pid) if conn.pid else None
                    active_ports.append({
                        "port": conn.laddr.port,
                        "address": conn.laddr.ip,
                        "pid": conn.pid,
                        "process_name": proc.name() if proc else None,
                        "status": conn.status
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    active_ports.append({
                        "port": conn.laddr.port,
                        "address": conn.laddr.ip,
                        "pid": conn.pid,
                        "process_name": None,
                        "status": conn.status
                    })
    except Exception as e:
        logger.error(f"활성 포트 목록 조회 중 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "success": True,
        "count": len(active_ports),
        "ports": active_ports
    }


@router.post("/port/auto-sync")
async def auto_sync_ports():
    """
    프론트엔드와 백엔드 포트 자동 동기화
    """
    # 백엔드 포트 범위
    backend_ports = range(8000, 8010)
    # 프론트엔드 포트 범위
    frontend_ports = range(5173, 5183)

    # 사용 가능한 백엔드 포트 찾기
    available_backend = find_available_ports(8000, 8009, 1)
    # 사용 가능한 프론트엔드 포트 찾기
    available_frontend = find_available_ports(5173, 5182, 1)

    if not available_backend:
        return {
            "success": False,
            "message": "사용 가능한 백엔드 포트를 찾을 수 없습니다"
        }

    if not available_frontend:
        return {
            "success": False,
            "message": "사용 가능한 프론트엔드 포트를 찾을 수 없습니다"
        }

    return {
        "success": True,
        "backend_port": available_backend[0],
        "frontend_port": available_frontend[0],
        "message": "포트 동기화 성공"
    }
