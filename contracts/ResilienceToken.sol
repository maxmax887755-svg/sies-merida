// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {ERC1155} from "@openzeppelin/contracts/token/ERC1155/ERC1155.sol";
import {AccessControl} from "@openzeppelin/contracts/access/AccessControl.sol";

/// @title ResilienceToken - creditos de resiliencia ecosistemica (SIES-Merida)
/// @notice Cada emision crea un nuevo id de token ERC-1155 ligado a un hash de evidencia.
contract ResilienceToken is ERC1155, AccessControl {
    bytes32 public constant VERIFICADOR_ROLE = keccak256("VERIFICADOR_ROLE");

    uint256 private _ultimoId;
    mapping(uint256 => string) private _evidencia;

    event CreditoEmitido(
        address indexed destinatario,
        uint256 indexed id,
        uint256 cantidad,
        string evidenciaHash
    );

    constructor(string memory uri_) ERC1155(uri_) {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(VERIFICADOR_ROLE, msg.sender);
    }

    /// @notice Emite creditos. Solo cuentas con VERIFICADOR_ROLE.
    function emitirCredito(
        address destinatario,
        uint256 cantidad,
        string calldata evidenciaHash
    ) external onlyRole(VERIFICADOR_ROLE) returns (uint256 id) {
        id = ++_ultimoId;
        _evidencia[id] = evidenciaHash;
        _mint(destinatario, id, cantidad, "");
        emit CreditoEmitido(destinatario, id, cantidad, evidenciaHash);
    }

    function evidenciaDe(uint256 id) external view returns (string memory) {
        return _evidencia[id];
    }

    function supportsInterface(bytes4 interfaceId)
        public
        view
        override(ERC1155, AccessControl)
        returns (bool)
    {
        return super.supportsInterface(interfaceId);
    }
}
