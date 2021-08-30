import React, { ReactNode } from 'react';
import {
    StyleSheet,
    ViewStyle,
    TextStyle,
    StatusBar,
    Platform,
    View,
    SafeAreaView,
} from 'react-native';
import { ScrollView } from 'react-native-gesture-handler';
import { KeyboardAwareScrollView } from 'react-native-keyboard-aware-scroll-view';
import LinearGradient from 'react-native-linear-gradient';
import { IconTypes } from '../assets/Images';
import Config from '../utils/Config';
import HeaderComponent from './reuse/HeaderComponent';

type Props = {
    enableScroll?: boolean;
    children: ReactNode;
    style?: ViewStyle;
    hasTextInput?: boolean;
    headerTitle: string | undefined;
    isHomeScreen?: boolean;
    safeAreaView?: boolean;
    leftIcon?: IconTypes;
    rightIcon?: IconTypes;
    onLeftPress?: () => void;
    onRightPress?: () => void;
    textStyle?: TextStyle
};

/** A Wrapper Component with BoilerPlate code for all Screens */
export function Container(props: Props) {

    const {
        children,
        enableScroll,
        style,
        hasTextInput,
        headerTitle,
        safeAreaView,
        leftIcon,
        rightIcon,
        onLeftPress,
        onRightPress,
        textStyle,
        isHomeScreen = false
    } = props;

    const containerStyle: ViewStyle = {
        ...styles.wrapper_style,
        ...style,
    };

    return (
        <>
            <LinearGradient
                style={styles.container}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 0 }}
                colors={[
                    Config.colors.HEADER_COLOR_1,
                    Config.colors.HEADER_COLOR_2
                ]}>
                <StatusBar
                    barStyle='light-content'
                    backgroundColor='transparent'
                    translucent />
            </LinearGradient>
            <HeaderComponent
                title={headerTitle}
                textStyle={textStyle}
                isHomeScreen={isHomeScreen}
                leftIcon={leftIcon}
                rightIcon={rightIcon}
                onLeftPress={onLeftPress}
                onRightPress={onRightPress} />
            <View style={containerStyle}>
                {hasTextInput ? (
                    <KeyboardAwareScrollView
                        enableAutomaticScroll={Platform.OS === 'ios'}
                        keyboardShouldPersistTaps={'handled'}
                        showsVerticalScrollIndicator={false}
                        bounces={false}
                        contentContainerStyle={style}
                        enableOnAndroid>
                        {children}
                    </KeyboardAwareScrollView>
                ) : (
                    <ScrollView
                        showsVerticalScrollIndicator={false}
                        scrollEnabled={enableScroll}
                        keyboardShouldPersistTaps="handled"
                        bounces={false}
                        contentContainerStyle={containerStyle}>
                        {children}
                    </ScrollView>
                )}
            </View>
            {safeAreaView && <SafeAreaView style={{ backgroundColor: 'white' }} />}
        </>
    );
}

const styles = StyleSheet.create({
    wrapper_style: {
        flex: 1,
        backgroundColor: Config.colors.WHITE,
    },
    container: {
        width: '100%',
        alignItems: 'center',
        justifyContent: 'flex-end',
    }
});

