#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
FlowDesk 自定义验证器模块

作用说明：
本模块提供专为FlowDesk定制的输入验证器类，用于实现输入框内容的实时验证与格式控制。
这些验证器严格遵循面向对象的设计原则，将复杂的验证逻辑封装在独立的类中，
确保UI层代码的整洁与分离。

核心设计：
- 实时禁止：在用户输入过程中，一旦输入内容即将变得不符合规范，就立即阻止该字符的输入。
- 状态反馈：通过返回不同的验证状态（Acceptable, Intermediate, Invalid），为UI提供精确的反馈依据。
- 可复用性：验证器可被应用到任何QLineEdit控件，实现UI组件的标准化和代码复用。
"""

from PyQt5.QtGui import QValidator
from ...utils.network_utils import validate_subnet_mask


class IPAddressValidator(QValidator):
    """
    IP地址实时输入验证器

    作用说明：
    这是一个高度智能的IP地址验证器，它能够在用户输入的每一个瞬间，实时判断
    输入内容是否符合IPv4地址的格式规范。其核心目标是“实时禁止”而非“事后提醒”，
    从根本上杜绝无效输入的可能性，提供流畅的用户体验。

    实现原理：
    继承QValidator并重写其validate方法。此方法会在输入框内容每次发生变化时
    被调用。我们通过解析当前的输入字符串，逐段（0-255的数字）和分隔符（.）
    进行逻辑判断，返回三种状态之一：
    - Invalid: 输入非法，该字符会被立即拒绝，无法显示在输入框中。
    - Intermediate: 输入内容是合法的中间状态（例如 "192.168."），允许用户继续输入。
    - Acceptable: 输入内容是一个完整且合法的IP地址（例如 "192.168.1.1"）。

    使用示例：
        ip_input = QLineEdit()
        ip_validator = IPAddressValidator()
        ip_input.setValidator(ip_validator)
    """

    def validate(self, input_text: str, pos: int) -> tuple:
        """
        重写的核心验证方法，在输入内容变化时被调用。

        参数说明：
            input_text (str): 输入框中包含新输入字符的完整文本。
            pos (int): 新字符被插入后的光标位置。

        返回值 (tuple)：
            一个包含 (状态, 文本, 光标位置) 的元组。
        """
        # 如果输入为空，是合法的中间状态，允许用户开始输入
        if not input_text:
            return (QValidator.Intermediate, input_text, pos)

        # 使用点（.）分割字符串，得到IP地址的各个段
        octets = input_text.split('.')

        # 检查段数是否超过4个，超过则无效
        if len(octets) > 4:
            return (QValidator.Invalid, input_text, pos)

        # 逐个检查每个段的有效性
        for i, octet in enumerate(octets):
            # 段内不能为空，除非是最后一段且整个IP未输入完整
            if not octet:
                # 如果空段不是最后一段（例如 "192..1.1"），则无效
                if i < len(octets) - 1:
                    return (QValidator.Invalid, input_text, pos)
                # 如果是最后一段为空（例如 "192.168.1."），是合法的中间状态
                continue

            # 检查段内是否只包含数字
            if not octet.isdigit():
                return (QValidator.Invalid, input_text, pos)

            # 检查段的数值是否在0-255之间
            # 这是实现“实时禁止”的核心，例如输入“257”时，
            # 当输入'7'后，int(octet)会变成257，判断>255，返回Invalid
            if int(octet) > 255:
                return (QValidator.Invalid, input_text, pos)

        # 检查IP地址是否是一个完整且合法的格式
        # 必须有4个段，且最后一位不能是点
        if len(octets) == 4 and all(octet for octet in octets) and not input_text.endswith('.'):
            return (QValidator.Acceptable, input_text, pos)
        else:
            # 其他所有情况（例如 "192.168." 或 "192.168.1.10"）都视为合法的中间状态
            return (QValidator.Intermediate, input_text, pos)


class SubnetMaskValidator(QValidator):
    """
    子网掩码实时输入验证器

    作用说明：
    专门用于验证子网掩码输入的验证器，支持点分十进制格式（如255.255.255.0）
    和CIDR格式（如/24）两种输入方式。实现实时输入阻止，确保用户只能输入
    符合子网掩码规范的内容。

    验证规则：
    1. 点分十进制格式：每段数值0-255，且必须是有效的子网掩码（连续的1后跟连续的0）
    2. CIDR格式：/0 到 /32 的有效前缀长度
    3. 实时阻止无效字符和超出范围的数值

    使用示例：
        mask_input = QLineEdit()
        mask_validator = SubnetMaskValidator()
        mask_input.setValidator(mask_validator)
    """

    def validate(self, input_text: str, pos: int) -> tuple:
        """
        子网掩码验证的核心逻辑实现

        参数说明：
            input_text (str): 当前输入框中的完整文本
            pos (int): 光标位置

        返回值 (tuple)：
            验证状态元组 (状态, 文本, 光标位置)
        """
        # 空输入允许，用户可以开始输入
        if not input_text:
            return (QValidator.Intermediate, input_text, pos)

        # 检查CIDR格式输入（以/开头）
        if input_text.startswith('/'):
            # 移除/前缀，检查数字部分
            cidr_part = input_text[1:]
            
            # 如果只有/，允许继续输入
            if not cidr_part:
                return (QValidator.Intermediate, input_text, pos)
            
            # 检查是否只包含数字
            if not cidr_part.isdigit():
                return (QValidator.Invalid, input_text, pos)
            
            # 检查CIDR值范围（0-32）
            cidr_value = int(cidr_part)
            if cidr_value > 32:
                return (QValidator.Invalid, input_text, pos)
            
            # 完整的CIDR格式
            return (QValidator.Acceptable, input_text, pos)

        # 处理点分十进制格式
        octets = input_text.split('.')
        
        # 超过4段无效
        if len(octets) > 4:
            return (QValidator.Invalid, input_text, pos)

        # 检查每个段
        for i, octet in enumerate(octets):
            # 空段处理
            if not octet:
                # 非最后段为空无效（如 "255..255.0"）
                if i < len(octets) - 1:
                    return (QValidator.Invalid, input_text, pos)
                continue

            # 只允许数字
            if not octet.isdigit():
                return (QValidator.Invalid, input_text, pos)

            # 数值范围检查（0-255）
            if int(octet) > 255:
                return (QValidator.Invalid, input_text, pos)

        # 完整的4段点分十进制格式需要进一步验证
        if len(octets) == 4 and all(octet for octet in octets) and not input_text.endswith('.'):
            # 使用network_utils验证是否为有效子网掩码
            if validate_subnet_mask(input_text):
                return (QValidator.Acceptable, input_text, pos)
            else:
                return (QValidator.Invalid, input_text, pos)

        # 其他情况为中间状态
        return (QValidator.Intermediate, input_text, pos)


class DNSValidator(QValidator):
    """
    DNS服务器地址实时输入验证器

    作用说明：
    专门用于验证DNS服务器IP地址输入的验证器。由于DNS服务器地址本质上就是
    IP地址，因此复用IP地址的验证逻辑，确保输入的DNS地址格式正确。

    验证特点：
    - 复用IPAddressValidator的验证逻辑
    - 支持IPv4地址格式验证
    - 实时阻止无效输入
    - 允许空输入（DNS可选配置）

    使用示例：
        dns_input = QLineEdit()
        dns_validator = DNSValidator()
        dns_input.setValidator(dns_validator)
    """

    def __init__(self):
        """初始化DNS验证器，内部使用IP地址验证器"""
        super().__init__()
        self._ip_validator = IPAddressValidator()

    def validate(self, input_text: str, pos: int) -> tuple:
        """
        DNS地址验证实现

        由于DNS服务器地址就是IP地址，直接委托给IP地址验证器处理。
        这种设计遵循了代码复用原则，避免重复实现相同的验证逻辑。

        参数说明：
            input_text (str): 当前输入的DNS地址
            pos (int): 光标位置

        返回值 (tuple)：
            验证状态元组
        """
        # 直接使用IP地址验证器的逻辑
        return self._ip_validator.validate(input_text, pos)
